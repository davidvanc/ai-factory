from pydantic import BaseModel

class HexRequest(BaseModel):
    hex: str

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
    hex: str
    rgb: RGB
    hsl: HSL
