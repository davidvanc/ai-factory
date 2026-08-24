import re
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field, StrictStr, model_validator
from src.logic import MAX_BULK_ITEMS


class ErrorItem(BaseModel):
    code: str
    message: str


class ValidateChecks(BaseModel):
    structure: bool
    country_supported: bool
    length: bool
    bban_format: bool
    mod97: bool


class ValidateRequest(BaseModel):
    iban: StrictStr


class ValidateResponse(BaseModel):
    input: str
    valid: bool
    iban: Optional[str] = None
    formatted: Optional[str] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    check_digits: Optional[str] = None
    bban: Optional[str] = None
    length: Optional[int] = None
    expected_length: Optional[int] = None
    bank_code: Optional[str] = None
    account_number: Optional[str] = None
    checks: ValidateChecks
    errors: List[ErrorItem] = Field(default_factory=list)


class BulkRequest(BaseModel):
    ibans: List[Any] = Field(default_factory=list, max_length=MAX_BULK_ITEMS)
    format_output: bool = True


class BulkItemResult(BaseModel):
    index: int
    input: Optional[str] = None
    status: Literal["valid", "invalid", "error"]
    valid: bool
    iban: Optional[str] = None
    formatted: Optional[str] = None
    country_code: Optional[str] = None
    errors: List[ErrorItem] = Field(default_factory=list)


class BulkSummary(BaseModel):
    total: int
    valid: int
    invalid: int
    errors: int


class BulkResponse(BaseModel):
    summary: BulkSummary
    results: List[BulkItemResult]


class FormatRequest(BaseModel):
    iban: StrictStr
    style: Literal["print", "electronic"] = "print"


class FormatResponse(BaseModel):
    input: str
    style: str
    formatted: str
    electronic: str
    valid: bool
    errors: List[ErrorItem] = Field(default_factory=list)


class GenerateCheckDigitsRequest(BaseModel):
    country_code: Optional[StrictStr] = None
    bban: Optional[StrictStr] = None
    iban: Optional[StrictStr] = None

    @model_validator(mode="after")
    def check_input_combination(self) -> "GenerateCheckDigitsRequest":
        has_iban = self.iban is not None and re.fullmatch(
            r"[A-Za-z0-9]{5,}", "".join(self.iban.split())
        ) is not None
        has_pair = (
            self.country_code is not None
            and self.bban is not None
            and re.fullmatch(r"[A-Za-z]{2}", "".join(self.country_code.split()))
            is not None
            and re.fullmatch(r"[A-Za-z0-9]+", "".join(self.bban.split())) is not None
        )
        if not (has_iban or has_pair):
            raise ValueError(
                "geef 'iban' (minimaal 5 alfanumerieke tekens) of 'country_code' (2 letters) plus 'bban' (alfanumeriek)"
            )
        return self


class GenerateCheckDigitsResponse(BaseModel):
    country_code: str
    bban: str
    check_digits: str
    iban: str
    formatted: str
    valid: bool
    errors: List[ErrorItem] = Field(default_factory=list)


class CountryEntry(BaseModel):
    country_code: str
    country_name: str
    iban_length: int
    bban_pattern: str
    bank_code_slice: List[int]
    sepa: bool
    example: str


class CountriesResponse(BaseModel):
    count: int
    countries: List[CountryEntry]


class StatusResponse(BaseModel):
    status: str
    version: str
    standards: List[str]
    countries_supported: int
    max_bulk_items: int
