from app.core.security import create_access_token, hash_password
from app.db.models.user import User

def test_cannot_create_duplicate_screen(client, session):
    manager = User(
        email="screenmanager@example.com",
        password_hash=hash_password("password123"),
        full_name="Screen Manager",
        role="manager",
    )

    session.add(manager)
    session.commit()
    session.refresh(manager)

    token = create_access_token(manager.id, manager.role)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    first_response = client.post(
        "/api/v1/screens",
        json={
            "name": "Screen 1",
            "total_seats": 100,
        },
        headers=headers,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/screens",
        json={
            "name": "Screen 1",
            "total_seats": 100,
        },
        headers=headers,
    )

    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"]
        == "Screen with this name already exists"
    )


def test_cannot_create_screen_with_zero_seats(client, session):
    manager = User(
        email="zeroseatmanager@example.com",
        password_hash=hash_password("password123"),
        full_name="Zero Seat Manager",
        role="manager",
    )

    session.add(manager)
    session.commit()
    session.refresh(manager)

    token = create_access_token(manager.id, manager.role)

    response = client.post(
        "/api/v1/screens",
        json={
            "name": "Empty Screen",
            "total_seats": 0,
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Total seats must be greater than zero"
    )