from fastapi import APIRouter
from src.models import EmailValidationRequest, EmailValidationResponse
from src.logic import validate_email
from src.service_template.logging_config import get_logger

log = get_logger("email_validator")
router = APIRouter()

@router.post("/validate", response_model=EmailValidationResponse, description="Valideert een e-mailadres volgens RFC 5322 regels. Retourneert of het adres geldig is en een reden indien ongeldig.")
async def validate_email_endpoint(request: EmailValidationRequest):
    log.info(f"Validating email: {request.email}")
    is_valid, reason = validate_email(request.email)
    return EmailValidationResponse(valid=is_valid, reason=reason)
