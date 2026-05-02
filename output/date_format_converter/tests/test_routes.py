from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_convert_iso_to_eu():
    response = client.post("/convert", json={
        "value": "2023-12-25",
        "from_format": "iso",
        "to_format": "eu"
    })
    assert response.status_code == 200
    assert response.json()["converted"] == "25-12-2023"

def test_convert_eu_to_us():
    response = client.post("/convert", json={
        "value": "25-12-2023",
        "from_format": "eu",
        "to_format": "us"
    })
    assert response.status_code == 200
    assert response.json()["converted"] == "12/25/2023"

def test_convert_us_to_unix():
    response = client.post("/convert", json={
        "value": "12/25/2023",
        "from_format": "us",
        "to_format": "unix"
    })
    assert response.status_code == 200
    assert response.json()["converted"] == "1703462400"

def test_convert_unix_to_iso():
    response = client.post("/convert", json={
        "value": "1703462400",
        "from_format": "unix",
        "to_format": "iso"
    })
    assert response.status_code == 200
    assert response.json()["converted"] == "2023-12-25"

def test_convert_invalid_date_format():
    response = client.post("/convert", json={
        "value": "invalid-date",
        "from_format": "eu",
        "to_format": "iso"
    })
    assert response.status_code == 400

def test_convert_unknown_format():
    response = client.post("/convert", json={
        "value": "25-12-2023",
        "from_format": "unknown",
        "to_format": "iso"
    })
    assert response.status_code == 422

def test_detect_format():
    cases = [
        ("2023-12-25", "iso"),
        ("25-12-2023", "eu"),
        ("12/25/2023", "us"),
        ("1703462400", "unix")
    ]
    for val, expected in cases:
        response = client.post("/detect", json={"value": val})
        assert response.status_code == 200
        assert response.json()["detected_format"] == expected

def test_detect_invalid_date():
    response = client.post("/detect", json={"value": "not-a-date"})
    assert response.status_code == 400

def test_get_formats():
    response = client.get("/formats")
    assert response.status_code == 200
    data = response.json()
    assert "formats" in data
    assert len(data["formats"]) == 4

def test_get_status():
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_leap_year():
    response = client.post("/convert", json={
        "value": "29-02-2024",
        "from_format": "eu",
        "to_format": "iso"
    })
    assert response.status_code == 200
    assert response.json()["converted"] == "2024-02-29"

def test_invalid_date_31_02_2023():
    response = client.post("/convert", json={
        "value": "31-02-2023",
        "from_format": "eu",
        "to_format": "iso"
    })
    assert response.status_code == 400
