import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

class TestMain:
    def test_root_endpoint_returns_welcome_message(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to Time API! Use /time to get the current time."}

    def test_time_endpoint_returns_200(self):
        response = client.get("/time")
        assert response.status_code == 200

    def test_time_response_contains_valid_iso8601(self):
        response = client.get("/time")
        data = response.json()
        assert "current_time" in data
        # Attempt to parse the ISO 8601 string; if it fails, test fails
        from datetime import datetime
        try:
            datetime.fromisoformat(data["current_time"])
        except ValueError:
            pytest.fail(f"Received invalid ISO 8601 time: {data['current_time']}")

    def test_api_returns_json_content_type(self):
        response = client.get("/time")
        assert response.headers["content-type"] == "application/json"
        response2 = client.get("/")
        assert response2.headers["content-type"] == "application/json"
