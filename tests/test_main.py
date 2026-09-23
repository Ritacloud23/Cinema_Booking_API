from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "ScreenHive API is running"
    }

def test_database_connection(session):
    assert session is not None    

def test_request_has_request_id(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert response.headers["x-request-id"]


def test_request_has_process_time(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "x-process-time" in response.headers

    process_time = float(response.headers["x-process-time"])
    assert process_time >= 0
