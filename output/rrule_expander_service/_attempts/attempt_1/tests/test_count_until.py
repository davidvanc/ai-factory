import pytest

def test_until_inclusive(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=DAILY;UNTIL=20240103T000000Z",
        "dtstart": "2024-01-01T00:00:00Z"
    })
    assert r.status_code == 200
    data = r.json()
    assert "2024-01-03T00:00:00+00:00" in data["occurrences"]

def test_count_and_until_mutually_exclusive(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=DAILY;COUNT=5;UNTIL=20240105T000000Z",
        "dtstart": "2024-01-01"
    })
    assert r.status_code == 422

def test_infinite_truncated(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=DAILY",
        "dtstart": "2024-01-01",
        "max_results": 10
    })
    assert r.status_code == 200
    data = r.json()
    assert data["truncated"] is True
    assert len(data["occurrences"]) == 10

def test_max_results_exceeds_limit(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=DAILY",
        "dtstart": "2024-01-01",
        "max_results": 20000
    })
    assert r.status_code == 422

def test_until_utc_with_tzaware_dtstart(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=DAILY;UNTIL=20240103T080000Z",
        "dtstart": "2024-01-01T09:00:00",
        "tzid": "Europe/Amsterdam"
    })
    assert r.status_code == 200
    data = r.json()
    assert "2024-01-03T09:00:00+01:00" in data["occurrences"]
    assert len(data["occurrences"]) == 3

def test_next_inclusive(client):
    r = client.post("/next", json={
        "rrule": "FREQ=DAILY",
        "dtstart": "2024-01-01T00:00:00Z",
        "from_datetime": "2024-01-05T00:00:00Z",
        "n": 2,
        "inclusive": True
    })
    assert r.status_code == 200
    data = r.json()
    assert data["occurrences"][0] == "2024-01-05T00:00:00+00:00"

def test_next_exclusive(client):
    r = client.post("/next", json={
        "rrule": "FREQ=DAILY",
        "dtstart": "2024-01-01T00:00:00Z",
        "from_datetime": "2024-01-05T00:00:00Z",
        "n": 2,
        "inclusive": False
    })
    assert r.status_code == 200
    data = r.json()
    assert data["occurrences"][0] == "2024-01-06T00:00:00+00:00"

def test_next_exhausted(client):
    r = client.post("/next", json={
        "rrule": "FREQ=DAILY;COUNT=3",
        "dtstart": "2024-01-01T00:00:00Z",
        "from_datetime": "2024-01-05T00:00:00Z",
        "n": 2
    })
    assert r.status_code == 200
    data = r.json()
    assert data["exhausted"] is True
    assert len(data["occurrences"]) == 0
