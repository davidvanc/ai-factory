from fastapi import APIRouter, HTTPException
from src.models import PasswordRequest, PasswordResponse
from src.logic import generate_password
from src.service_template.logging_config import get_logger

log = get_logger("password_generator")
router = APIRouter()

@router.post("/generate", response_model=PasswordResponse)
async def generate_password_endpoint(request: PasswordRequest):
    log.info(f"Generating password of length {request.length}")
    try:
        password = generate_password(
            length=request.length,
            include_digits=request.include_digits,
            include_uppercase=request.include_uppercase,
            include_lowercase=request.include_lowercase,
            include_symbols=request.include_symbols
        )
        return PasswordResponse(password=password, length=len(password))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
