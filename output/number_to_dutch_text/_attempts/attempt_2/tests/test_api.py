from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_convert_200():
    response = client.get("/convert?number=1.50")
    assert response.status_code == 200
    assert response.json() == {"text": "één komma vijftig"}


def test_invalid_input_400():
    response = client.get("/convert?number=abc")
    assert response.status_code == 400
