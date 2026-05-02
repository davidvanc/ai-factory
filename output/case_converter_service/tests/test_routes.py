from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_post_convert_uppercase():
    response = client.post("/convert", json={"text": "hello world example", "target_case": "upper"})
    assert response.status_code == 200
    assert response.json()["result"] == "HELLO WORLD EXAMPLE"

def test_post_convert_lowercase():
    response = client.post("/convert", json={"text": "HELLO WORLD EXAMPLE", "target_case": "lower"})
    assert response.status_code == 200
    assert response.json()["result"] == "hello world example"

def test_post_convert_titlecase():
    response = client.post("/convert", json={"text": "hello world example", "target_case": "title"})
    assert response.status_code == 200
    assert response.json()["result"] == "Hello World Example"

def test_post_convert_snakecase():
    response = client.post("/convert", json={"text": "hello world example", "target_case": "snake"})
    assert response.status_code == 200
    assert response.json()["result"] == "hello_world_example"

def test_post_convert_kebabcase():
    response = client.post("/convert", json={"text": "hello world example", "target_case": "kebab"})
    assert response.status_code == 200
    assert response.json()["result"] == "hello-world-example"

def test_post_convert_camelcase():
    response = client.post("/convert", json={"text": "hello world example", "target_case": "camel"})
    assert response.status_code == 200
    assert response.json()["result"] == "helloWorldExample"

def test_post_convert_missing_fields():
    response = client.post("/convert", json={"text": "hello world"})
    assert response.status_code == 422

def test_post_convert_invalid_target_case():
    response = client.post("/convert", json={"text": "hello world", "target_case": "invalid_case"})
    assert response.status_code == 400

def test_post_convert_all():
    response = client.post("/convert/all", json={"text": "hello world example"})
    assert response.status_code == 200
    data = response.json()
    assert data["original"] == "hello world example"
    assert data["upper"] == "HELLO WORLD EXAMPLE"
    assert data["lower"] == "hello world example"
    assert data["title"] == "Hello World Example"
    assert data["snake"] == "hello_world_example"
    assert data["kebab"] == "hello-world-example"
    assert data["camel"] == "helloWorldExample"

def test_get_cases():
    response = client.get("/cases")
    assert response.status_code == 200
    data = response.json()
    assert "supported_cases" in data
    assert "upper" in data["supported_cases"]
    assert "camel" in data["supported_cases"]

def test_get_status():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "case_converter_service"
