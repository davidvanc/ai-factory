from pydantic import BaseModel, Field, model_validator

class PasswordRequest(BaseModel):
    length: int = Field(..., ge=8, le=128)
    include_digits: bool = True
    include_uppercase: bool = True
    include_lowercase: bool = True
    include_symbols: bool = True

    @model_validator(mode='after')
    def check_at_least_one_group(self):
        if not (self.include_digits or self.include_uppercase or self.include_lowercase or self.include_symbols):
            raise ValueError('At least one character group must be enabled')
        return self

class PasswordResponse(BaseModel):
    password: str
    length: int
