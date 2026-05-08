from fastapi import APIRouter
from src.models import ScheduleRequest, ScheduleResponse, ConflictResponse
from src.logic import schedule_tasks, detect_conflicts
from src.service_template.logging_config import get_logger

log = get_logger("task_scheduler")
router = APIRouter()

@router.post("/schedule", response_model=ScheduleResponse)
def schedule(request: ScheduleRequest):
    log.info(f"Scheduling {len(request.tasks)} tasks")
    scheduled, failed = schedule_tasks(request.tasks)
    return ScheduleResponse(scheduled=scheduled, failed=failed)

@router.post("/detect-conflicts", response_model=ConflictResponse)
def conflicts(request: ScheduleRequest):
    log.info(f"Detecting conflicts for {len(request.tasks)} tasks")
    detected = detect_conflicts(request.tasks)
    return ConflictResponse(conflicts=detected, total_conflicts=len(detected))
