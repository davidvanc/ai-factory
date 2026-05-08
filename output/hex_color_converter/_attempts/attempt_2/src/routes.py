from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional
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
async def convert_both(request: Request, hex: Optional[str] = Query(None, description="Hex color code")):
    if hex is None:
        try:
            body = await request.json()
            if isinstance(body, dict):
                hex = body.get("hex")
        except Exception:
            pass
            
    if hex is None:
        raise HTTPException(status_code=422, detail="hex is required")
        
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
