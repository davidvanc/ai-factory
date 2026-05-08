from fastapi import APIRouter
from src.models import DayOfWeekRequest, DayOfWeekResponse
from src.logic import calculate_day_of_week_zeller

router = APIRouter()

@router.post("/day-of-week", response_model=DayOfWeekResponse)
async def get_day_of_week(request: DayOfWeekRequest):
    day_name = calculate_day_of_week_zeller(
        year=request.date.year,
        month=request.date.month,
        day=request.date.day
    )
    return DayOfWeekResponse(
        date=request.date.isoformat(),
        day_of_week=day_name
    )
