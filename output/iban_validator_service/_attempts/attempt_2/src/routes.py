import os
from fastapi import APIRouter, HTTPException, Query
from src import logic
from src.country_registry import all_countries, country_count, get_country
from src.models import (
    BulkRequest,
    BulkResponse,
    CountriesResponse,
    CountryEntry,
    FormatRequest,
    FormatResponse,
    IbanRequest,
    StatusResponse,
    ValidateResponse,
)

SERVICE_NAME = "iban_validator_service"
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
SPEC_LABEL = "ISO 13616 / ISO 7064 mod-97-10"
router = APIRouter()


@router.get("/status", response_model=StatusResponse)
def get_status() -> dict:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "spec": SPEC_LABEL,
        "supported_countries": country_count(),
    }


@router.post("/validate", response_model=ValidateResponse)
def post_validate(payload: IbanRequest) -> dict:
    return logic.validate_iban(payload.iban)


@router.get("/validate", response_model=ValidateResponse)
def get_validate(iban: str = Query(...)) -> dict:
    return logic.validate_iban(iban)


@router.post("/format", response_model=FormatResponse)
def post_format(payload: FormatRequest) -> dict:
    res = logic.validate_iban(payload.iban)
    formatted = logic.format_iban(res["compact"], payload.style)
    return {
        "input": payload.iban,
        "style": payload.style,
        "formatted": formatted,
        "compact": res["compact"],
        "valid": res["valid"],
        "errors": res["errors"],
    }


@router.post("/validate/bulk", response_model=BulkResponse)
def post_validate_bulk(payload: BulkRequest) -> dict:
    return logic.validate_bulk(payload.ibans, payload.style, payload.fail_fast)


@router.get("/countries", response_model=CountriesResponse)
def get_countries() -> dict:
    entries = all_countries()
    return {"count": len(entries), "countries": entries}


@router.get("/countries/{country_code}", response_model=CountryEntry)
def get_country_entry(country_code: str) -> dict:
    entry = get_country(country_code)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"Landcode '{country_code.upper()}' staat niet in de ISO 13616 registry",
        )
    return entry
