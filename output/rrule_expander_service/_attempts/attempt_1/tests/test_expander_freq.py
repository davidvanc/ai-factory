import pytest

def test_expand_daily_count_5(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=DAILY;COUNT=5",
        "dtstart": "2024-01-01"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 5
    assert data["occurrences"] == [
        "2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"
    ]

def test_expand_weekly_interval_byday(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE,FR;COUNT=6",
        "dtstart": "2024-01-01T09:00:00",
        "tzid": "Europe/Amsterdam"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 6
    assert data["occurrences"] == [
        "2024-01-01T09:00:00+01:00",
        "2024-01-03T09:00:00+01:00",
        "2024-01-05T09:00:00+01:00",
        "2024-01-15T09:00:00+01:00",
        "2024-01-17T09:00:00+01:00",
        "2024-01-19T09:00:00+01:00"
    ]

def test_expand_yearly_bymonth_byday(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=YEARLY;BYMONTH=11;BYDAY=1TU",
        "dtstart": "2024-11-01"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["occurrences"][0] == "2024-11-05"

def test_tzid_dst_transition(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=DAILY;COUNT=3",
        "dtstart": "2024-03-30T09:00:00",
        "tzid": "Europe/Amsterdam"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["occurrences"] == [
        "2024-03-30T09:00:00+01:00",
        "2024-03-31T09:00:00+02:00",
        "2024-04-01T09:00:00+02:00"
    ]

def test_invalid_tzid(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=DAILY;COUNT=1",
        "dtstart": "2024-01-01T09:00:00",
        "tzid": "Invalid/Timezone"
    })
    assert r.status_code == 422
    assert "Invalid TZID" in r.json()["detail"]
