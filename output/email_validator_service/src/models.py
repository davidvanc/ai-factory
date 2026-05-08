from pydantic import BaseModel, Field

class EmailValidationRequest(BaseModel):
    email: str = Field(..., description="The email address to validate")

class EmailValidationResponse(BaseModel):
    valid: bool = Field(..., description="Whether the email is valid")
    reason: str = Field(..., description="Reason for validation result")
