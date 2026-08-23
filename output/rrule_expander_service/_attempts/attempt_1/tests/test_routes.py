import pytest

def test_openapi_schema(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert "/expand" in schema["paths"]
    assert "/next" in schema["paths"]
    assert "/validate" in schema["paths"]
    assert "/describe" in schema["paths"]
    assert "/recurrence-set/expand" in schema["paths"]
    assert "/expand/batch" in schema["paths"]
    assert "/status" in schema["paths"]

def test_status(client):
    r = client.get("/status")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "FREQ" in data["supported_parts"]
    assert "UNTIL" in data["supported_parts"]

def test_missing_fields_422(client):
    r = client.post("/expand", json={"rrule": "FREQ=DAILY"})
    assert r.status_code == 422

def test_get_expand(client):
    r = client.get("/expand?rrule=FREQ=DAILY;COUNT=2&dtstart=2024-01-01")
    assert r.status_code == 200
    assert len(r.json()["occurrences"]) == 2

def test_batch_expand(client):
    r = client.post("/expand/batch", json={
        "items": [
            {"id": "a", "rrule": "FREQ=DAILY;COUNT=2", "dtstart": "2024-01-01"},
            {"id": "b", "rrule": "FREQ=BOGUS;COUNT=2", "dtstart": "2024-01-01"}
        ]
    })
    assert r.status_code == 200
    data = r.json()
    assert data["results"][0]["ok"] is True
    assert data["results"][1]["ok"] is False
    assert "error" in data["results"][1]

def test_batch_too_many(client):
    items = [{"id": str(i), "rrule": "FREQ=DAILY;COUNT=1", "dtstart": "2024-01-01"} for i in range(101)]
    r = client.post("/expand/batch", json={"items": items})
    assert r.status_code == 422

def test_window_after_before(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=DAILY;COUNT=10",
        "dtstart": "2024-01-01",
        "after": "2024-01-03",
        "before": "2024-01-05"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["occurrences"] == ["2024-01-03", "2024-01-04", "2024-01-05"]
