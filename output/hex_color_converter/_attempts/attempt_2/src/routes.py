from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from src.logic import hex_to_rgb, hex_to_hsl

router = APIRouter()

class HexRequest(BaseModel):
    hex: str = Field(..., description="Hex color code")

class RGBModel(BaseModel):
    r: int
    g: int
    b: int

class HSLModel(BaseModel):
    h: int
    s: int
    l: int

class RGBResponse(BaseModel):
    rgb: RGBModel

class HSLResponse(BaseModel):
    hsl: HSLModel

class ConvertResponse(BaseModel):
    hex: str
    rgb: RGBModel
    hsl: HSLModel

@router.post("/to-rgb", response_model=RGBResponse)
async def to_rgb(request: HexRequest):
    try:
        rgb = hex_to_rgb(request.hex)
        return RGBResponse(rgb=RGBModel(**rgb))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/to-hsl", response_model=HSLResponse)
async def to_hsl(request: HexRequest):
    try:
        hsl = hex_to_hsl(request.hex)
        return HSLResponse(hsl=HSLModel(**hsl))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/convert", response_model=ConvertResponse)
async def convert(hex: str = Query(..., description="Hex color code")):
    try:
        rgb = hex_to_rgb(hex)
        hsl = hex_to_hsl(hex)
        return ConvertResponse(hex=hex, rgb=RGBModel(**rgb), hsl=HSLModel(**hsl))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
