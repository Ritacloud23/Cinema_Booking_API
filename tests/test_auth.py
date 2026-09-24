from app.cache.redis import redis_client
from app.core.security import hash_password
from app.db.models.user import User


def test_login_is_rate_limited(client, session):
    user = User(
        email="ratelimit@example.com",
        password_hash=hash_password("password123"),
        full_name="Rate Limit User",
        role="moviegoer",
    )

    session.add(user)
    session.commit()

    redis_key = "rate_limit:login:ratelimit@example.com"
    redis_client.delete(redis_key)

    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "ratelimit@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 200

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "ratelimit@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"

    redis_client.delete(redis_key)

def test_failed_login_attempts_are_rate_limited(client, session):
    user = User(
        email="failedlogin@example.com",
        password_hash=hash_password("password123"),
        full_name="Failed Login User",
        role="moviegoer",
    )
    session.add(user)
    session.commit()

    redis_key = "rate_limit:login:failedlogin@example.com"
    redis_client.delete(redis_key)

    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "failedlogin@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "failedlogin@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"

    redis_client.delete(redis_key)


def test_rate_limit_is_separate_for_different_users(client, session):
    user_one = User(
        email="userone@example.com",
        password_hash=hash_password("password123"),
        full_name="User One",
        role="moviegoer",
    )

    user_two = User(
        email="usertwo@example.com",
        password_hash=hash_password("password123"),
        full_name="User Two",
        role="moviegoer",
    )

    session.add(user_one)
    session.add(user_two)
    session.commit()

    key_one = "rate_limit:login:userone@example.com"
    key_two = "rate_limit:login:usertwo@example.com"

    redis_client.delete(key_one)
    redis_client.delete(key_two)

    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "userone@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 200

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "userone@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 429

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "usertwo@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    redis_client.delete(key_one)
    redis_client.delete(key_two)


def test_cannot_register_with_existing_email(client):
    first_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "full_name": "First User",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "full_name": "Second User",
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email already registered"   


