from fastapi import APIRouter, Query
from src.models import ISBNRequest, ISBNResponse
from src.logic import check_isbn

router = APIRouter()

@router.post("/validate", response_model=ISBNResponse)
async def validate_isbn_post(request: ISBNRequest):
    """
    Valideert een ISBN-10 of ISBN-13 code. Accepteert input met of zonder hyphens/spaties.
    Retourneert of de code geldig is en welk formaat het is.
    """
    result = check_isbn(request.isbn)
    return ISBNResponse(**result)

@router.get("/validate", response_model=ISBNResponse)
async def validate_isbn_get(isbn: str = Query(..., description="The ISBN code to validate")):
    """
    Valideert een ISBN-10 of ISBN-13 code via query parameter.
    """
    result = check_isbn(isbn)
    return ISBNResponse(**result)
