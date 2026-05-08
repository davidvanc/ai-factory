from fastapi import APIRouter, HTTPException
from src.models import DayOfWeekRequest, DayOfWeekResponse
from src.logic import calculate_day_of_week
import datetime

router = APIRouter()

@router.post("/day-of-week", response_model=DayOfWeekResponse)
async def get_day_of_week(request: DayOfWeekRequest):
    try:
        datetime.datetime.strptime(request.date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Non-existent date")
    
    day = calculate_day_of_week(request.date)
    return DayOfWeekResponse(day=day)
