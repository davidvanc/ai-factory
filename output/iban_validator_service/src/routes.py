from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from src.errors import NOT_A_STRING
from src.iban_registry import IBAN_REGISTRY, get_country
from src.logic import MAX_BULK_ITEMS, SERVICE_VERSION, STANDARDS, calculate_check_digits, format_print, normalize_iban, validate_iban
from src.models import (BulkItemResult, BulkRequest, BulkResponse, BulkSummary, CountriesResponse, CountryEntry, FormatRequest, FormatResponse, GenerateCheckDigitsRequest, GenerateCheckDigitsResponse, StatusResponse, ValidateRequest, ValidateResponse)

router = APIRouter(tags=["iban"])

def _bulk_status(result: Dict[str, Any]) -> str:
    if result["errors"] and result["errors"][0]["code"] == NOT_A_STRING:
        return "error"
    elif result["valid"]:
        return "valid"
    else:
        return "invalid"

@router.post("/validate", response_model=ValidateResponse)
def validate_endpoint(payload: ValidateRequest) -> ValidateResponse:
    result = validate_iban(payload.iban)
    return ValidateResponse(**result)

@router.post("/validate/bulk", response_model=BulkResponse)
def bulk_endpoint(payload: BulkRequest) -> BulkResponse:
    results: List[BulkItemResult] = []
    valid_count = 0
    invalid_count = 0
    error_count = -0
    for index, item in enumerate(payload.ibans):
        result = validate_iban(item)
        status = _bulk_status(result)
        if status == "valid":
            valid_count += 1
        elif status == "invalid":
            invalid_count += 1
        else:
            error_count += 1
        results.append(
            BulkItemResult(
                index=index,
                input=result["input"],
                status=status,
                valid=result["valid"],
                iban=result["iban"],
                formatted=result["formatted"] if payload.format_output else None,
                country_code=result["country_code"],
                errors=result["errors"],
            )
        )
    summary = BulkSummary(
        total=len(payload.ibans),
        valid=valid_count,
        invalid=invalid_count,
        errors=error_count,
    )
    return BulkResponse(summary=summary, results=results)

@router.post("/format", response_model=FormatResponse)
def format_endpoint(payload: FormatRequest) -> FormatResponse:
    result = validate_iban(payload.iban)
    electronic = result["iban"] if result["iban"] is not None else normalize_iban(payload.iban)
    formatted = format_print(electronic) if payload.style == "print" else electronic
    return FormatResponse(
        input=payload.iban,
        style=payload.style,
        formatted=formatted,
        electronic=electronic,
        valid=result["valid"],
        errors=result["errors"],
    )

@router.post("/generate-check-digits", response_model=GenerateCheckDigitsResponse)
def generate_check_digits_endpoint(payload: GenerateCheckDigitsRequest) -> GenerateCheckDigitsResponse:
    if payload.iban is not None and len(normalize_iban(payload.iban)) >= 5:
        compact = normalize_iban(payload.iban)
        country_code = compact[:2]
        bban = compact[4:]
    else:
        country_code = normalize_iban(payload.country_code)
        bban = normalize_iban(payload.bban)
    check_digits = calculate_check_digits(country_code, bban)
    iban = country_code + check_digits + bban
    result = validate_iban(iban)
    return GenerateCheckDigitsResponse(
        country_code=country_code,
        bban=bban,
        check_digits=check_digits,
        iban=iban,
        formatted=format_print(iban),
        valid=result["valid"],
        errors=result["errors"],
    )

@router.get("/countries", response_model=CountriesResponse)
def countries_endpoint(country: Optional[str] = Query(default=None)) -> CountriesResponse:
    def build_entry(code: str, entry: Dict[str, Any]) -> CountryEntry:
        return CountryEntry(
            country_code=code,
            country_name=entry["country_name"],
            iban_length=entry["iban_length"],
            bban_pattern=entry["bban_pattern"],
            bank_code_slice=list(entry["bank_code_slice"]),
            sepa=entry["sepa"],
            example=entry["example"],
        )
    entries: List[CountryEntry] = []
    if country is not None:
        code = country.strip().upper()
        entry = get_country(code)
        if entry is not None:
            entries.append(build_entry(code, entry))
    else:
        for code in sorted(IBAN_REGISTRY.keys()):
            entries.append(build_entry(code, IBAN_REGISTRY[code]))
    return CountriesResponse(count=len(entries), countries=entries)

@router.get("/status", response_model=StatusResponse)
def status_endpoint() -> StatusResponse:
    return StatusResponse(
        status="ok",
        version=SERVICE_VERSION,
        standards=list(STANDARDS),
        countries_supported=len(IBAN_REGISTRY),
        max_bulk_items=MAX_BULK_ITEMS,
    )
