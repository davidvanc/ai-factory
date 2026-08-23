EMPTY_INPUT: str = "EMPTY_INPUT"
INVALID_BASE64_CHARACTER: str = "INVALID_BASE64_CHARACTER"
INVALID_PADDING: str = "INVALID_PADDING"
NOT_UTF8_DECODABLE: str = "NOT_UTF8_DECODABLE"


class Base64Error(Exception):
    def __init__(self, error_code: str, message: str, detail: str) -> None:
        self.error_code = error_code
        self.message = message
        self.detail = detail
        super().__init__(message)


def error_payload(exc: Base64Error) -> dict[str, str]:
    return {"error_code": exc.error_code, "message": exc.message, "detail": exc.detail}
