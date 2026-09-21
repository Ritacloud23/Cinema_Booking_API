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