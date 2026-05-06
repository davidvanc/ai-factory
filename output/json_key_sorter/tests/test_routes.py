def test_sort_keys_flat_object(client):
    payload = {
        "data": {
            "banana": 1,
            "apple": 2,
            "cherry": 3
        }
    }
    response = client.post("/sort-keys", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["keys"] == ["apple", "banana", "cherry"]
    assert list(data["sorted"].keys()) == ["apple", "banana", "cherry"]

def test_sort_keys_recursive(client):
    payload = {
        "data": {
            "cherry": {
                "zeta": 0,
                "alpha": 1
            },
            "apple": 2,
            "banana": 1
        }
    }
    response = client.post("/sort-keys", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["keys"] == ["apple", "banana", "cherry"]
    assert list(data["sorted"]["cherry"].keys()) == ["alpha", "zeta"]

def test_sort_keys_empty_object(client):
    payload = {"data": {}}
    response = client.post("/sort-keys", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["keys"] == []
    assert data["sorted"] == {}

def test_sort_keys_missing_data(client):
    payload = {"wrong_key": {"a": 1}}
    response = client.post("/sort-keys", json=payload)
    assert response.status_code == 422

def test_sort_keys_non_object(client):
    # Test with list
    response = client.post("/sort-keys", json={"data": ["a", "b"]})
    assert response.status_code == 422
    
    # Test with string
    response2 = client.post("/sort-keys", json={"data": "not an object"})
    assert response2.status_code == 422

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
