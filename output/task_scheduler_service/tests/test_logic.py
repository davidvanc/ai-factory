from datetime import datetime
from src.models import TaskInput
from src.logic import check_overlap, detect_conflicts, schedule_tasks

def test_check_overlap():
    start1 = datetime(2026, 3, 7, 10, 0)
    end1 = datetime(2026, 3, 7, 11, 0)
    start2 = datetime(2026, 3, 7, 10, 30)
    end2 = datetime(2026, 3, 7, 11, 30)
    
    overlap = check_overlap(start1, end1, start2, end2)
    assert overlap == 30

def test_detect_conflicts_logic():
    tasks = [
        TaskInput(name="A", start_time=datetime(2026, 3, 7, 10, 0), duration=60, priority=5),
        TaskInput(name="B", start_time=datetime(2026, 3, 7, 10, 30), duration=30, priority=4)
    ]
    conflicts = detect_conflicts(tasks)
    assert len(conflicts) == 1
    assert conflicts[0].task_a == "A"
    assert conflicts[0].task_b == "B"
    assert conflicts[0].overlap_minutes == 30

def test_schedule_tasks_logic():
    tasks = [
        TaskInput(name="Panel", start_time=datetime(2026, 3, 7, 10, 0), duration=60, priority=5),
        TaskInput(name="Meetup", start_time=datetime(2026, 3, 7, 10, 30), duration=45, priority=2),
        TaskInput(name="Workshop", start_time=datetime(2026, 3, 7, 12, 0), duration=90, priority=4)
    ]
    scheduled, failed = schedule_tasks(tasks)
    assert len(scheduled) == 3
    assert len(failed) == 0
    
    panel = next(t for t in scheduled if t.name == "Panel")
    assert panel.status == "Scheduled"
    
    meetup = next(t for t in scheduled if t.name == "Meetup")
    assert meetup.status == "Rescheduled"
    assert meetup.start_time == datetime(2026, 3, 7, 11, 0)
