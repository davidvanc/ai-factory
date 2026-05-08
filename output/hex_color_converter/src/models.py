from pydantic import BaseModel, Field

class HexRequest(BaseModel):
    hex: str = Field(..., pattern=r'^#?[0-9a-fA-F]{6}$')

class RGB(BaseModel):
    r: int
    g: int
    b: int

class HSL(BaseModel):
    h: int
    s: int
    l: int

class RGBResponse(BaseModel):
    rgb: RGB

class HSLResponse(BaseModel):
    hsl: HSL

class ConvertResponse(BaseModel):
    rgb: RGB
    hsl: HSL
