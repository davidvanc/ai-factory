import pytest

def test_rrule_prefix_and_lowercase(client):
    r = client.post("/validate", json={
        "rrule": "rrule:freq=daily;count=2",
        "dtstart": "2024-01-01"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is True
    assert data["parts"]["FREQ"] == "DAILY"

def test_interval_zero_invalid(client):
    r = client.post("/validate", json={
        "rrule": "FREQ=DAILY;INTERVAL=0",
        "dtstart": "2024-01-01"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is False
    assert any("INTERVAL" in e for e in data["errors"])

def test_byday_ordinal_weekly_invalid(client):
    r = client.post("/validate", json={
        "rrule": "FREQ=WEEKLY;BYDAY=2MO",
        "dtstart": "2024-01-01"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is False
    assert any("ordinal" in e for e in data["errors"])

def test_validate_bogus_freq(client):
    r = client.post("/validate", json={
        "rrule": "FREQ=BOGUS",
        "dtstart": "2024-01-01"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is False

def test_validate_missing_freq(client):
    r = client.post("/validate", json={
        "rrule": "COUNT=5",
        "dtstart": "2024-01-01"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is False

def test_validate_infinite(client):
    r = client.post("/validate", json={
        "rrule": "FREQ=DAILY",
        "dtstart": "2024-01-01"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["infinite"] is True
