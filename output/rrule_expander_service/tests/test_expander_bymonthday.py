import pytest

def test_expand_monthly_bymonthday_negative(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=MONTHLY;BYMONTHDAY=-1;COUNT=4",
        "dtstart": "2024-01-31"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["occurrences"] == [
        "2024-01-31", "2024-02-29", "2024-03-31", "2024-04-30"
    ]

def test_expand_monthly_bymonthday_31_skips(client):
    r = client.post("/expand", json={
        "rrule": "FREQ=MONTHLY;BYMONTHDAY=31;COUNT=3",
        "dtstart": "2024-01-31"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["occurrences"] == [
        "2024-01-31", "2024-03-31", "2024-05-31"
    ]
