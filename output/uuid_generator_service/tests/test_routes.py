import pytest
from fastapi.testclient import TestClient
import uuid

from src.main import app

client = TestClient(app)

def test_generate_valid_uuid_v4():
    response = client.post("/generate", json={})
    assert response.status_code == 200
    data = response.json()
    assert "uuid" in data
    
    val = data["uuid"]
    try:
        parsed_uuid = uuid.UUID(val, version=4)
        assert str(parsed_uuid) == val
    except ValueError:
        pytest.fail("Returned string is not a valid UUID v4")

def test_generate_batch_10_unique():
    response = client.post("/generate-batch", json={"count": 10})
    assert response.status_code == 200
    data = response.json()
    assert "uuids" in data
    assert "count" in data
    assert data["count"] == 10
    assert len(data["uuids"]) == 10
    
    assert len(set(data["uuids"])) == 10
    
    for val in data["uuids"]:
        try:
            parsed_uuid = uuid.UUID(val, version=4)
            assert str(parsed_uuid) == val
        except ValueError:
            pytest.fail("Returned string is not a valid UUID v4")

def test_generate_batch_count_0():
    response = client.post("/generate-batch", json={"count": 0})
    assert response.status_code == 422

def test_generate_batch_count_1001():
    response = client.post("/generate-batch", json={"count": 1001})
    assert response.status_code == 422

def test_generate_batch_missing_count():
    response = client.post("/generate-batch", json={})
    assert response.status_code == 422
