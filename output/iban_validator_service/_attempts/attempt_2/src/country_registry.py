from typing import Any, Dict, List, Optional, Tuple

_BASE_ENTRIES: Tuple[Dict[str, Any], ...] = (
    {"country_code": "AD", "name": "Andorra", "iban_length": 24, "bban_pattern": "8!n12!c", "bban_regex": "^[0-9]{8}[A-Z0-9]{12}$", "sepa": True, "example": "AD1200012030200359100100", "bank_length": 4, "branch_length": 4},
    {"country_code": "AE", "name": "United Arab Emirates", "iban_length": 23, "bban_pattern": "3!n16!n", "bban_regex": "^[0-9]{19}$", "sepa": False, "example": "AE070331234567890123456", "bank_length": 3, "branch_length": 0},
    {"country_code": "AL", "name": "Albania", "iban_length": 28, "bban_pattern": "8!n16!c", "bban_regex": "^[0-9]{8}[A-Z0-9]{16}$", "sepa": False, "example": "AL47212110090000000235698741", "bank_length": 3, "branch_length": 4},
    {"country_code": "AT", "name": "Austria", "iban_length": 20, "bban_pattern": "16!n", "bban_regex": "^[0-9]{16}$", "sepa": True, "example": "AT611904300234573201", "bank_length": 5, "branch_length": 0},
    {"country_code": "AZ", "name": "Azerbaijan", "iban_length": 28, "bban_pattern": "4!a20!c", "bban_regex": "^[A-Z]{4}[A-Z0-9]{20}$", "sepa": False, "example": "AZ21NABZ00000000137010001944", "bank_length": 4, "branch_length": 0},
    {"country_code": "BA", "name": "Bosnia and Herzegovina", "iban_length": 20, "bban_pattern": "16!n", "bban_regex": "^[0-9]{16}$", "sepa": False, "example": "BA391290079401028494", "bank_length": 3, "branch_length": 3},
    {"country_code": "BE", "name": "Belgium", "iban_length": 16, "bban_pattern": "12!n", "bban_regex": "^[0-9]{12}$", "sepa": True, "example": "BE68539007547034", "bank_length": 3, "branch_length": 0},
    {"country_code": "BG", "name": "Bulgaria", "iban_length": 22, "bban_pattern": "4!a6!n8!c", "bban_regex": "^[A-Z]{4}[0-9]{6}[A-Z0-9]{8}$", "sepa": True, "example": "BG80BNBG96611020345678", "bank_length": 4, "branch_length": 4},
    {"country_code": "CH", "name": "Switzerland", "iban_length": 21, "bban_pattern": "5!n12!c", "bban_regex": "^[0-9]{5}[A-Z0-9]{12}$", "sepa": True, "example": "CH9300762011623852957", "bank_length": 5, "branch_length": 0},
    {"country_code": "CY", "name": "Cyprus", "iban_length": 28, "bban_pattern": "8!n16!c", "bban_regex": "^[0-9]{8}[A-Z0-9]{16}$", "sepa": True, "example": "CY17002001280000001200527600", "bank_length": 3, "branch_length": 5},
    {"country_code": "CZ", "name": "Czechia", "iban_length": 24, "bban_pattern": "20!n", "bban_regex": "^[0-9]{20}$", "sepa": True, "example": "CZ6508000000192000145399", "bank_length": 4, "branch_length": 0},
    {"country_code": "DE", "name": "Germany", "iban_length": 22, "bban_pattern": "18!n", "bban_regex": "^[0-9]{18}$", "sepa": True, "example": "DE89370400440532013000", "bank_length": 8, "branch_length": 0},
    {"country_code": "DK", "name": "Denmark", "iban_length": 18, "bban_pattern": "14!n", "bban_regex": "^[0-9]{14}$", "sepa": True, "example": "DK5000400440116243", "bank_length": 4, "branch_length": 0},
    {"country_code": "EE", "name": "Estonia", "iban_length": 20, "bban_pattern": "16!n", "bban_regex": "^[0-9]{16}$", "sepa": True, "example": "EE382200221020145685", "bank_length": 2, "branch_length": 0},
    {"country_code": "ES", "name": "Spain", "iban_length": 24, "bban_pattern": "20!n", "bban_regex": "^[0-9]{20}$", "sepa": True, "example": "ES9121000418450200051332", "bank_length": 4, "branch_length": 4},
    {"country_code": "FI", "name": "Finland", "iban_length": 18, "bban_pattern": "14!n", "bban_regex": "^[0-9]{14}$", "sepa": True, "example": "FI2112345600000785", "bank_length": 3, "branch_length": 0},
    {"country_code": "FO", "name": "Faroe Islands", "iban_length": 18, "bban_pattern": "14!n", "bban_regex": "^[0-9]{14}$", "sepa": False, "example": "FO6264600001631634", "bank_length": 4, "branch_length": 0},
    {"country_code": "FR", "name": "France", "iban_length": 27, "bban_pattern": "10!n11!c2!n", "bban_regex": "^[0-9]{10}[A-Z0-9]{11}[0-9]{2}$", "sepa": True, "example": "FR1420041010050500013M02606", "bank_length": 5, "branch_length": 5},
    {"country_code": "GB", "name": "United Kingdom", "iban_length": 22, "bban_pattern": "4!a14!n", "bban_regex": "^[A-Z]{4}[0-9]{14}$", "sepa": True, "example": "GB29NWBK60161331926819", "bank_length": 4, "branch_length": 6},
    {"country_code": "GE", "name": "Georgia", "iban_length": 22, "bban_pattern": "2!a16!n", "bban_regex": "^[A-Z]{2}[0-9]{16}$", "sepa": False, "example": "GE29NB0000000101904917", "bank_length": 2, "branch_length": 0},
    {"country_code": "GI", "name": "Gibraltar", "iban_length": 23, "bban_pattern": "4!a15!c", "bban_regex": "^[A-Z]{4}[A-Z0-9]{15}$", "sepa": True, "example": "GI75NWBK000000007099453", "bank_length": 4, "branch_length": 0},
    {"country_code": "GL", "name": "Greenland", "iban_length": 18, "bban_pattern": "14!n", "bban_regex": "^[0-9]{14}$", "sepa": False, "example": "GL8964710001000206", "bank_length": 4, "branch_length": 0},
    {"country_code": "GR", "name": "Greece", "iban_length": 27, "bban_pattern": "7!n16!c", "bban_regex": "^[0-9]{7}[A-Z0-9]{16}$", "sepa": True, "example": "GR1601101250000000012300695", "bank_length": 3, "branch_length": 4},
    {"country_code": "HR", "name": "Croatia", "iban_length": 21, "bban_pattern": "17!n", "bban_regex": "^[0-9]{17}$", "sepa": True, "example": "HR1210010051863000160", "bank_length": 7, "branch_length": 0},
    {"country_code": "HU", "name": "Hungary", "iban_length": 28, "bban_pattern": "24!n", "bban_regex": "^[0-9]{24}$", "sepa": True, "example": "HU42117730161111101800000000", "bank_length": 3, "branch_length": 4},
    {"country_code": "IE", "name": "Ireland", "iban_length": 22, "bban_pattern": "4!a14!n", "bban_regex": "^[A-Z]{4}[0-9]{14}$", "sepa": True, "example": "IE29AIBK93115212345678", "bank_length": 4, "branch_length": 6},
    {"country_code": "IL", "name": "Israel", "iban_length": 23, "bban_pattern": "19!n", "bban_regex": "^[0-9]{19}$", "sepa": False, "example": "IL620108000000099999999", "bank_length": 3, "branch_length": 3},
    {"country_code": "IS", "name": "Iceland", "iban_length": 26, "bban_pattern": "22!n", "bban_regex": "^[0-9]{22}$", "sepa": True, "example": "IS140159260076545510730339", "bank_length": 4, "branch_length": 2},
    {"country_code": "IT", "name": "Italy", "iban_length": 27, "bban_pattern": "1!a10!n12!c", "bban_regex": "^[A-Z][0-9]{10}[A-Z0-9]{12}$", "sepa": True, "example": "IT60X0542811101000000123456", "bank_length": 6, "branch_length": 5},
    {"country_code": "LI", "name": "Liechtenstein", "iban_length": 21, "bban_pattern": "5!n12!c", "bban_regex": "^[0-9]{5}[A-Z0-9]{12}$", "sepa": True, "example": "LI21088100002324013AA", "bank_length": 5, "branch_length": 0},
    {"country_code": "LT", "name": "Lithuania", "iban_length": 20, "bban_pattern": "16!n", "bban_regex": "^[0-9]{16}$", "sepa": True, "example": "LT121000011101001000", "bank_length": 5, "branch_length": 0},
    {"country_code": "LU", "name": "Luxembourg", "iban_length": 20, "bban_pattern": "3!n13!c", "bban_regex": "^[0-9]{3}[A-Z0-9]{13}$", "sepa": True, "example": "LU280019400644750000", "bank_length": 3, "branch_length": 0},
    {"country_code": "LV", "name": "Latvia", "iban_length": 21, "bban_pattern": "4!a13!c", "bban_regex": "^[A-Z]{4}[A-Z0-9]{13}$", "sepa": True, "example": "LV80BANK0000435195001", "bank_length": 4, "branch_length": 0},
    {"country_code": "MC", "name": "Monaco", "iban_length": 27, "bban_pattern": "10!n11!c2!n", "bban_regex": "^[0-9]{10}[A-Z0-9]{11}[0-9]{2}$", "sepa": True, "example": "MC5811222000010123456789030", "bank_length": 5, "branch_length": 5},
    {"country_code": "ME", "name": "Montenegro", "iban_length": 22, "bban_pattern": "18!n", "bban_regex": "^[0-9]{18}$", "sepa": False, "example": "ME25505000012345678951", "bank_length": 3, "branch_length": 0},
    {"country_code": "MT", "name": "Malta", "iban_length": 31, "bban_pattern": "4!a5!n18!c", "bban_regex": "^[A-Z]{4}[0-9]{5}[A-Z0-9]{18}$", "sepa": True, "example": "MT84MALT011000012345MTLCAST001S", "bank_length": 4, "branch_length": 5},
    {"country_code": "NL", "name": "Netherlands", "iban_length": 18, "bban_pattern": "4!a10!n", "bban_regex": "^[A-Z]{4}[0-9]{10}$", "sepa": True, "example": "NL91ABNA0417164300", "bank_length": 4, "branch_length": 0},
    {"country_code": "NO", "name": "Norway", "iban_length": 15, "bban_pattern": "11!n", "bban_regex": "^[0-9]{11}$", "sepa": True, "example": "NO9386011117947", "bank_length": 4, "branch_length": 0},
    {"country_code": "PL", "name": "Poland", "iban_length": 28, "bban_pattern": "24!n", "bban_regex": "^[0-9]{24}$", "sepa": True, "example": "PL61109010140000071219812874", "bank_length": 8, "branch_length": 0},
    {"country_code": "PT", "name": "Portugal", "iban_length": 25, "bban_pattern": "21!n", "bban_regex": "^[0-9]{21}$", "sepa": True, "example": "PT50000201231234567890154", "bank_length": 4, "branch_length": 4},
    {"country_code": "RO", "name": "Romania", "iban_length": 24, "bban_pattern": "4!a16!c", "bban_regex": "^[A-Z]{4}[A-Z0-9]{16}$", "sepa": True, "example": "RO49AAAA1B31007593840000", "bank_length": 4, "branch_length": 0},
    {"country_code": "RS", "name": "Serbia", "iban_length": 22, "bban_pattern": "18!n", "bban_regex": "^[0-9]{18}$", "sepa": False, "example": "RS35260005601001611379", "bank_length": 3, "branch_length": 0},
    {"country_code": "SE", "name": "Sweden", "iban_length": 24, "bban_pattern": "20!n", "bban_regex": "^[0-9]{20}$", "sepa": True, "example": "SE4550000000058398257466", "bank_length": 3, "branch_length": 0},
    {"country_code": "SI", "name": "Slovenia", "iban_length": 19, "bban_pattern": "15!n", "bban_regex": "^[0-9]{15}$", "sepa": True, "example": "SI56263300012039086", "bank_length": 5, "branch_length": 0},
    {"country_code": "SK", "name": "Slovakia", "iban_length": 24, "bban_pattern": "20!n", "bban_regex": "^[0-9]{20}$", "sepa": True, "example": "SK3112000000198742637541", "bank_length": 4, "branch_length": 6},
    {"country_code": "SM", "name": "San Marino", "iban_length": 27, "bban_pattern": "1!a10!n12!c", "bban_regex": "^[A-Z][0-9]{10}[A-Z0-9]{12}$", "sepa": True, "example": "SM86U0322509800000000270100", "bank_length": 6, "branch_length": 5},
    {"country_code": "TR", "name": "Turkey", "iban_length": 26, "bban_pattern": "5!n17!c", "bban_regex": "^[0-9]{5}[A-Z0-9]{17}$", "sepa": False, "example": "TR330006100519786457841326", "bank_length": 5, "branch_length": 0},
    {"country_code": "VG", "name": "Virgin Islands, British", "iban_length": 24, "bban_pattern": "4!a16!n", "bban_regex": "^[A-Z]{4}[0-9]{16}$", "sepa": False, "example": "VG96VPVG0000012345678901", "bank_length": 4, "branch_length": 0},
)

REGISTRY: Dict[str, Dict[str, Any]] = {}

def reset_state() -> None:
    REGISTRY.clear()
    REGISTRY.update({entry["country_code"]: dict(entry) for entry in _BASE_ENTRIES})

def get_country(country_code: str) -> Optional[Dict[str, Any]]:
    if country_code is None or not isinstance(country_code, str):
        return None
    key = country_code.strip().upper()
    return REGISTRY.get(key)

def all_countries() -> List[Dict[str, Any]]:
    return sorted(REGISTRY.values(), key=lambda e: e["country_code"])

def country_count() -> int:
    return len(REGISTRY)

reset_state()
