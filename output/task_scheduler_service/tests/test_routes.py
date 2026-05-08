import pytest

def test_schedule_no_conflicts(client):
    payload = {
        "tasks": [
            {"name": "A", "start_time": "2026-03-07T10:00:00", "duration": 60, "priority": 3},
            {"name": "B", "start_time": "2026-03-07T11:00:00", "duration": 60, "priority": 3}
        ]
    }
    response = client.post("/schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["scheduled"]) == 2
    assert len(data["failed"]) == 0
    assert data["scheduled"][0]["status"] == "Scheduled"
    assert data["scheduled"][1]["status"] == "Scheduled"

def test_schedule_keeps_highest_priority(client):
    payload = {
        "tasks": [
            {"name": "Low", "start_time": "2026-03-07T10:00:00", "duration": 60, "priority": 1},
            {"name": "High", "start_time": "2026-03-07T10:00:00", "duration": 60, "priority": 5}
        ]
    }
    response = client.post("/schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    high = next(t for t in data["scheduled"] if t["name"] == "High")
    low = next(t for t in data["scheduled"] if t["name"] == "Low")
    
    assert high["status"] == "Scheduled"
    assert high["start_time"] == "2026-03-07T10:00:00"
    
    assert low["status"] == "Rescheduled"
    assert low["start_time"] == "2026-03-07T11:00:00"

def test_schedule_moves_lower_priority(client):
    payload = {
        "tasks": [
            {"name": "Panel", "start_time": "2026-03-07T10:00:00", "duration": 60, "priority": 5},
            {"name": "Meetup", "start_time": "2026-03-07T10:30:00", "duration": 45, "priority": 2}
        ]
    }
    response = client.post("/schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    meetup = next(t for t in data["scheduled"] if t["name"] == "Meetup")
    assert meetup["start_time"] == "2026-03-07T11:00:00"

def test_schedule_marks_failed_if_cannot_move(client):
    payload = {
        "tasks": [
            {"name": "Blocker", "start_time": "2026-03-07T10:00:00", "duration": 1440, "priority": 5},
            {"name": "Victim", "start_time": "2026-03-07T10:00:00", "duration": 60, "priority": 1}
        ]
    }
    response = client.post("/schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["scheduled"]) == 1
    assert len(data["failed"]) == 1
    assert data["failed"][0]["name"] == "Victim"

def test_detect_conflicts_overlap_minutes(client):
    payload = {
        "tasks": [
            {"name": "Task A", "start_time": "2026-03-22T09:00:00", "duration": 60, "priority": 3},
            {"name": "Task B", "start_time": "2026-03-22T09:30:00", "duration": 30, "priority": 4}
        ]
    }
    response = client.post("/detect-conflicts", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_conflicts"] == 1
    assert data["conflicts"][0]["overlap_minutes"] == 30

def test_detect_conflicts_empty_on_no_conflicts(client):
    payload = {
        "tasks": [
            {"name": "Task A", "start_time": "2026-03-22T09:00:00", "duration": 60, "priority": 3},
            {"name": "Task B", "start_time": "2026-03-22T10:00:00", "duration": 30, "priority": 4}
        ]
    }
    response = client.post("/detect-conflicts", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_conflicts"] == 0
    assert len(data["conflicts"]) == 0

def test_invalid_input_priority(client):
    payload = {
        "tasks": [
            {"name": "Task A", "start_time": "2026-03-22T09:00:00", "duration": 60, "priority": 6}
        ]
    }
    response = client.post("/schedule", json=payload)
    assert response.status_code == 422

def test_missing_fields(client):
    payload = {
        "tasks": [
            {"name": "Task A", "duration": 60, "priority": 3}
        ]
    }
    response = client.post("/schedule", json=payload)
    assert response.status_code == 422

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200

def test_realistic_open_data_day_events(client):
    payload = {
        "tasks": [
            {"name": "ODD Hackathon", "start_time": "2026-03-07T09:00:00", "duration": 480, "priority": 5},
            {"name": "Open Data Intro", "start_time": "2026-03-07T10:00:00", "duration": 60, "priority": 3},
            {"name": "Data Viz Workshop", "start_time": "2026-03-07T11:00:00", "duration": 120, "priority": 4},
            {"name": "Closing Keynote", "start_time": "2026-03-07T16:00:00", "duration": 60, "priority": 5}
        ]
    }
    response = client.post("/schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["scheduled"]) == 4
    assert len(data["failed"]) == 0
    
    hackathon = next(t for t in data["scheduled"] if t["name"] == "ODD Hackathon")
    keynote = next(t for t in data["scheduled"] if t["name"] == "Closing Keynote")
    workshop = next(t for t in data["scheduled"] if t["name"] == "Data Viz Workshop")
    intro = next(t for t in data["scheduled"] if t["name"] == "Open Data Intro")
    
    assert hackathon["start_time"] == "2026-03-07T09:00:00"
    assert keynote["start_time"] == "2026-03-07T17:00:00"
    assert workshop["start_time"] == "2026-03-07T18:00:00"
    assert intro["start_time"] == "2026-03-07T20:00:00"
