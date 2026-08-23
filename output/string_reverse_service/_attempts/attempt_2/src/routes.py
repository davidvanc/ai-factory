from fastapi import APIRouter, Query
from src.models import (
    ReverseRequest,
    ReverseResponse,
    BatchReverseRequest,
    BatchReverseResponse,
    BatchReverseItem,
    StatusResponse
)
from src.logic import perform_reverse
from src.service_template.logging_config import get_logger

log = get_logger("routes")

router = APIRouter()

@router.post("/reverse", response_model=ReverseResponse)
async def reverse_post(request: ReverseRequest):
    log.info(f"Reversing string of length {len(request.text)}, unicode_safe={request.unicode_safe}")
    reversed_text = perform_reverse(request.text, request.unicode_safe)
    return ReverseResponse(
        original=request.text,
        reversed=reversed_text,
        length=len(request.text),
        unicode_safe=request.unicode_safe
    )

@router.post("/reverse/batch", response_model=BatchReverseResponse)
async def reverse_batch(request: BatchReverseRequest):
    log.info(f"Batch reversing {len(request.items)} strings, unicode_safe={request.unicode_safe}")
    results = []
    for item in request.items:
        reversed_text = perform_reverse(item, request.unicode_safe)
        results.append(BatchReverseItem(
            original=item,
            reversed=reversed_text,
            length=len(item)
        ))
    return BatchReverseResponse(
        results=results,
        count=len(results),
        unicode_safe=request.unicode_safe
    )

@router.get("/reverse", response_model=ReverseResponse)
async def reverse_get(
    text: str = Query(..., max_length=10000, description="The string to reverse"),
    unicode_safe: bool = Query(False, description="If true, reverses by grapheme clusters")
):
    log.info(f"Reversing string of length {len(text)} via GET, unicode_safe={unicode_safe}")
    reversed_text = perform_reverse(text, unicode_safe)
    return ReverseResponse(
        original=text,
        reversed=reversed_text,
        length=len(text),
        unicode_safe=unicode_safe
    )

@router.get("/status", response_model=StatusResponse)
async def get_status():
    return StatusResponse(
        status="ok",
        service="string_reverse_service",
        version="1.0.0"
    )
