from typing import Any, Dict

EMPTY_INPUT = "EMPTY_INPUT"
INVALID_CHARACTERS = "INVALID_CHARACTERS"
INVALID_STRUCTURE = "INVALID_STRUCTURE"
UNKNOWN_COUNTRY = "UNKNOWN_COUNTRY"
INVALID_LENGTH = "INVALID_LENGTH"
INVALID_FORMAT = "INVALID_FORMAT"
INVALID_CHECK_DIGITS = "INVALID_CHECK_DIGITS"
CHECKSUM_FAILED = "CHECKSUM_FAILED"
NOT_A_STRING = "NOT_A_STRING"
INTERNAL_ERROR = "INTERNAL_ERROR"

MESSAGES: Dict[str, str] = {
    EMPTY_INPUT: "IBAN is leeg na normalisatie",
    INVALID_CHARACTERS: "IBAN bevat tekens buiten A-Z en 0-9",
    INVALID_STRUCTURE: "IBAN moet bestaan uit 2 letters, 2 cijfers en minimaal 1 BBAN-teken",
    UNKNOWN_COUNTRY: "Landcode '{country_code}' staat niet in de ISO 13616 registry",
    INVALID_LENGTH: "Lengte {length} wijkt af van verwachte lengte {expected_length} voor land {country_code}",
    INVALID_FORMAT: "BBAN '{bban}' matcht niet met patroon {bban_pattern} voor land {country_code}",
    INVALID_CHECK_DIGITS: "Controlecijfers '{check_digits}' zijn ongeldig (00, 01 en 99 zijn niet toegestaan)",
    CHECKSUM_FAILED: "mod-97 checksum is niet gelijk aan 1",
    NOT_A_STRING: "Item is geen string",
    INTERNAL_ERROR: "Onverwachte fout bij verwerken van item: {detail}"
}

def make_error(code: str, **kwargs: Any) -> Dict[str, str]:
    return {"code": code, "message": MESSAGES[code].format(**kwargs)}
