from fastapi import APIRouter, HTTPException, Query
from src.models import HexRequest, RGBResponse, HSLResponse, ConvertResponse, RGB, HSL
from src.logic import hex_to_rgb, rgb_to_hsl, clean_hex

router = APIRouter()

@router.post("/to-rgb", response_model=RGBResponse)
async def convert_to_rgb(request: HexRequest):
    try:
        r, g, b = hex_to_rgb(request.hex)
        return RGBResponse(rgb=RGB(r=r, g=g, b=b))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/to-hsl", response_model=HSLResponse)
async def convert_to_hsl(request: HexRequest):
    try:
        r, g, b = hex_to_rgb(request.hex)
        h, s, l = rgb_to_hsl(r, g, b)
        return HSLResponse(hsl=HSL(h=h, s=s, l=l))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/convert", response_model=ConvertResponse)
async def convert_both(hex: str = Query(..., description="Hex color code")):
    try:
        cleaned = clean_hex(hex)
        r, g, b = hex_to_rgb(hex)
        h, s, l = rgb_to_hsl(r, g, b)
        return ConvertResponse(
            hex=f"#{cleaned}",
            rgb=RGB(r=r, g=g, b=b),
            hsl=HSL(h=h, s=s, l=l)
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
