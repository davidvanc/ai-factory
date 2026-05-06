from pydantic import BaseModel

class HashRequest(BaseModel):
    text: str

class HashResponse(BaseModel):
    text: str
    md5: str

class StatusResponse(BaseModel):
    status: str
