def test_day_of_week_wednesday(client):
    response = client.post("/day-of-week", json={"date": "2025-01-15"})
    assert response.status_code == 200
    assert response.json() == {"day": "Wednesday"}

def test_day_of_week_saturday(client):
    response = client.post("/day-of-week", json={"date": "2000-01-01"})
    assert response.status_code == 200
    assert response.json() == {"day": "Saturday"}

def test_day_of_week_jan_feb_adjustment(client):
    response = client.post("/day-of-week", json={"date": "2023-02-01"})
    assert response.status_code == 200
    assert response.json() == {"day": "Wednesday"}

def test_day_of_week_leap_year(client):
    response = client.post("/day-of-week", json={"date": "2024-02-29"})
    assert response.status_code == 200
    assert response.json() == {"day": "Thursday"}

def test_invalid_date_format(client):
    response = client.post("/day-of-week", json={"date": "15-01-2025"})
    assert response.status_code == 422

def test_missing_date_field(client):
    response = client.post("/day-of-week", json={})
    assert response.status_code == 422

def test_non_existent_date(client):
    response = client.post("/day-of-week", json={"date": "2025-02-30"})
    assert response.status_code == 400
