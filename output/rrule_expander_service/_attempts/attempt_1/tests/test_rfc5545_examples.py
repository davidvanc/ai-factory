import pytest

def test_wkst_difference(client):
    r1 = client.post("/expand", json={
        "rrule": "FREQ=WEEKLY;INTERVAL=2;WKST=MO;BYDAY=TU,SU;COUNT=4",
        "dtstart": "1997-08-05T09:00:00"
    })
    r2 = client.post("/expand", json={
        "rrule": "FREQ=WEEKLY;INTERVAL=2;WKST=SU;BYDAY=TU,SU;COUNT=4",
        "dtstart": "1997-08-05T09:00:00"
    })
    assert r1.json()["occurrences"] != r2.json()["occurrences"]
