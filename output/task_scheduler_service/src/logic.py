from datetime import timedelta
from typing import List, Tuple
from src.models import TaskInput, ScheduledTask, Conflict

def get_end_time(start_time, duration_minutes):
    return start_time + timedelta(minutes=duration_minutes)

def check_overlap(start1, end1, start2, end2) -> int:
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)
    if overlap_start < overlap_end:
        return int((overlap_end - overlap_start).total_seconds() / 60)
    return 0

def detect_conflicts(tasks: List[TaskInput]) -> List[Conflict]:
    conflicts = []
    n = len(tasks)
    for i in range(n):
        for j in range(i + 1, n):
            t1 = tasks[i]
            t2 = tasks[j]
            end1 = get_end_time(t1.start_time, t1.duration)
            end2 = get_end_time(t2.start_time, t2.duration)
            overlap = check_overlap(t1.start_time, end1, t2.start_time, end2)
            if overlap > 0:
                conflicts.append(Conflict(
                    task_a=t1.name,
                    task_b=t2.name,
                    overlap_minutes=overlap
                ))
    return conflicts

def schedule_tasks(tasks: List[TaskInput]) -> Tuple[List[ScheduledTask], List[TaskInput]]:
    sorted_tasks = sorted(tasks, key=lambda x: (-x.priority, x.start_time))
    
    scheduled = []
    failed = []
    
    for task in sorted_tasks:
        current_start = task.start_time
        max_start = task.start_time + timedelta(hours=24)
        duration_td = timedelta(minutes=task.duration)
        
        is_scheduled = False
        
        while current_start < max_start:
            current_end = current_start + duration_td
            
            overlap_found = False
            next_possible_start = current_start
            
            for s_task in scheduled:
                if check_overlap(current_start, current_end, s_task.start_time, s_task.end_time) > 0:
                    overlap_found = True
                    if s_task.end_time > next_possible_start:
                        next_possible_start = s_task.end_time
            
            if not overlap_found:
                status = "Scheduled" if current_start == task.start_time else "Rescheduled"
                scheduled.append(ScheduledTask(
                    name=task.name,
                    start_time=current_start,
                    end_time=current_end,
                    duration=task.duration,
                    priority=task.priority,
                    status=status
                ))
                is_scheduled = True
                break
            else:
                if next_possible_start == current_start:
                    next_possible_start += timedelta(minutes=1)
                current_start = next_possible_start
                
        if not is_scheduled:
            failed.append(task)
            
    scheduled.sort(key=lambda x: x.start_time)
    return scheduled, failed
