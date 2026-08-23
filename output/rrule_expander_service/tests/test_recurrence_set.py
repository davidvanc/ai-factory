import pytest

def test_recurrence_set_expand(client):
    r = client.post("/recurrence-set/expand", json={
        "dtstart": "2024-03-01T12:00:00Z",
        "rrules": ["FREQ=WEEKLY;BYDAY=FR;COUNT=4"],
        "rdates": ["2024-03-06T12:00:00Z"],
        "exdates": ["2024-03-15T12:00:00Z"],
        "max_results": 50
    })
    assert r.status_code == 200
    data = r.json()
    assert "2024-03-06T12:00:00+00:00" in data["occurrences"]
    assert "2024-03-15T12:00:00+00:00" not in data["occurrences"]
    assert "2024-03-15T12:00:00+00:00" in data["excluded"]

def test_recurrence_set_multiple_rrules(client):
    r = client.post("/recurrence-set/expand", json={
        "dtstart": "2024-01-01",
        "rrules": ["FREQ=DAILY;COUNT=2", "FREQ=WEEKLY;COUNT=2"],
        "max_results": 50
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data["occurrences"]) == 3
