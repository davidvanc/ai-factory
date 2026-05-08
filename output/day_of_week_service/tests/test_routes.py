def test_post_day_of_week_friday(client):
    response = client.post("/day-of-week", json={"date": "2024-03-15"})
    assert response.status_code == 200
    assert response.json() == {"date": "2024-03-15", "day_of_week": "Friday"}

def test_post_day_of_week_monday(client):
    response = client.post("/day-of-week", json={"date": "2000-01-03"})
    assert response.status_code == 200
    assert response.json() == {"date": "2000-01-03", "day_of_week": "Monday"}

def test_post_day_of_week_leap_year(client):
    response = client.post("/day-of-week", json={"date": "2020-02-29"})
    assert response.status_code == 200
    assert response.json() == {"date": "2020-02-29", "day_of_week": "Saturday"}

def test_invalid_date_format(client):
    response = client.post("/day-of-week", json={"date": "2024/03/15"})
    assert response.status_code in (400, 422)

def test_non_existent_date(client):
    response = client.post("/day-of-week", json={"date": "2024-02-30"})
    assert response.status_code in (400, 422)

def test_missing_date_field(client):
    response = client.post("/day-of-week", json={})
    assert response.status_code == 422
