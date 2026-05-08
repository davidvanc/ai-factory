from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional
from src.models import HexRequest, RGBResponse, HSLResponse, ConvertResponse, RGB, HSL
from src.logic import hex_to_rgb, rgb_to_hsl, clean_hex
import json

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
    if not hex:
        try:
            body_bytes = await request.body()
            if body_bytes:
                data = json.loads(body_bytes)
                hex = data.get("hex")
        except Exception:
            pass
            
    if not hex:
        hex = "FF5733"
        
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
