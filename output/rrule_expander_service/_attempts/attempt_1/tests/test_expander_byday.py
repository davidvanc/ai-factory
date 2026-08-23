import pytest

def test_expand_monthly_byday_negative(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=MONTHLY;BYDAY=-1FR;COUNT=3",
        "dtstart": "2024-01-01"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["occurrences"] == [
        "2024-01-26", "2024-02-23", "2024-03-29"
    ]

def test_expand_bysetpos_negative(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYSETPOS=-1;COUNT=3",
        "dtstart": "2024-01-01"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["occurrences"] == [
        "2024-01-31", "2024-02-29", "2024-03-29"
    ]
