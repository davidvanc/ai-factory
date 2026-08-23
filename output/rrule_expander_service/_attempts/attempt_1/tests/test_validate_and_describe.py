import pytest

def test_describe_nl(client):
    r = client.post("/describe", json={
        "rrule": "FREQ=MONTHLY;BYDAY=-1FR;UNTIL=20241231T235959Z",
        "dtstart": "2024-01-01T10:00:00Z",
        "locale": "nl"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["text"] == "Elke maand op de laatste vrijdag, tot en met 31 december 2024"

def test_describe_en(client):
    r = client.post("/describe", json={
        "rrule": "FREQ=DAILY",
        "dtstart": "2024-01-01",
        "locale": "en"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["text"] != ""
