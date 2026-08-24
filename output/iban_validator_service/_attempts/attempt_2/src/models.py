import os
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr

MAX_BULK_ITEMS: int = int(os.getenv("IBAN_MAX_BULK_ITEMS", "100"))

class ErrorItem(BaseModel):
    code: StrictStr
    message: StrictStr

class IbanRequest(BaseModel):
    iban: StrictStr

class ValidateResponse(BaseModel):
    input: str
    valid: bool
    country_code: Optional[str] = None
    check_digits: Optional[str] = None
    bban: Optional[str] = None
    length: int
    expected_length: Optional[int] = None
    checksum_mod97: Optional[int] = None
    formatted: str
    compact: str
    bank_identifier: Optional[str] = None
    branch_identifier: Optional[str] = None
    account_number: Optional[str] = None
    errors: List[ErrorItem]

class FormatRequest(BaseModel):
    iban: StrictStr
    style: Literal["print", "compact", "electronic"] = "print"

class FormatResponse(BaseModel):
    input: str
    style: str
    formatted: str
    compact: str
    valid: bool
    errors: List[ErrorItem]

class BulkRequest(BaseModel):
    ibans: List[Any] = Field(..., max_length=MAX_BULK_ITEMS)
    style: Literal["print", "compact", "electronic"] = "print"
    fail_fast: StrictBool = False

class BulkItemResult(BaseModel):
    index: int
    input: Any = None
    status: Literal["valid", "invalid", "error"]
    valid: bool
    country_code: Optional[str] = None
    formatted: Optional[str] = None
    compact: Optional[str] = None
    length: Optional[int] = None
    expected_length: Optional[int] = None
    errors: List[ErrorItem]

class BulkSummary(BaseModel):
    valid: int
    invalid: int
    errors: int
    stopped_early: bool

class BulkResponse(BaseModel):
    count: int
    summary: BulkSummary
    results: List[BulkItemResult]

class CountryEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    country_code: str
    name: str
    iban_length: int
    bban_pattern: str
    bban_regex: str
    sepa: bool
    example: str

class CountriesResponse(BaseModel):
    count: int
    countries: List[CountryEntry]

class StatusResponse(BaseModel):
    status: str
    service: str
    version: str
    spec: str
    supported_countries: int
