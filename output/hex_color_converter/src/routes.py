from fastapi import APIRouter, Query
from src.models import HexRequest, RGBResponse, HSLResponse, ConvertResponse, RGB, HSL
from src.logic import hex_to_rgb, hex_to_hsl
from src.service_template.logging_config import get_logger

log = get_logger("hex_color_converter")
router = APIRouter()

@router.post("/to-rgb", response_model=RGBResponse)
async def convert_to_rgb(request: HexRequest):
    log.info(f"Converting {request.hex} to RGB")
    rgb_dict = hex_to_rgb(request.hex)
    return RGBResponse(rgb=RGB(**rgb_dict))

@router.post("/to-hsl", response_model=HSLResponse)
async def convert_to_hsl(request: HexRequest):
    log.info(f"Converting {request.hex} to HSL")
    hsl_dict = hex_to_hsl(request.hex)
    return HSLResponse(hsl=HSL(**hsl_dict))

@router.get("/convert", response_model=ConvertResponse)
async def convert_both(hex: str = Query(..., pattern=r'^#?[0-9a-fA-F]{6}$')):
    log.info(f"Converting {hex} to RGB and HSL")
    rgb_dict = hex_to_rgb(hex)
    hsl_dict = hex_to_hsl(hex)
    return ConvertResponse(rgb=RGB(**rgb_dict), hsl=HSL(**hsl_dict))
