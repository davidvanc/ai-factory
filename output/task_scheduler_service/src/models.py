from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

class TaskInput(BaseModel):
    name: str
    start_time: datetime
    duration: int = Field(..., gt=0, description="Duration in minutes")
    priority: int = Field(..., ge=1, le=5, description="Priority from 1 to 5")

class ScheduleRequest(BaseModel):
    tasks: List[TaskInput]

class ScheduledTask(BaseModel):
    name: str
    start_time: datetime
    end_time: datetime
    duration: int
    priority: int
    status: str

class ScheduleResponse(BaseModel):
    scheduled: List[ScheduledTask]
    failed: List[TaskInput]

class Conflict(BaseModel):
    task_a: str
    task_b: str
    overlap_minutes: int

class ConflictResponse(BaseModel):
    conflicts: List[Conflict]
    total_conflicts: int
