from datetime import datetime, timedelta

import pytest

from app.core.security import hash_password
from app.db.models.film import Film
from app.db.models.screen import Screen
from app.db.models.seat_inventory import SeatInventory
from app.db.models.showtime import Showtime
from app.db.models.user import User
from app.services.booking_service import create_booking
from app.services.hold_service import create_hold


def test_user_can_create_hold(session):
    user = User(
        email="holduser@example.com",
        password_hash=hash_password("password123"),
        full_name="Hold User",
        role="moviegoer",
    )

    film = Film(
        title="Hold Test Film",
        description="A test film",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Hold Test Screen",
        total_seats=10,
    )

    session.add(user)
    session.add(film)
    session.add(screen)
    session.commit()

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        ticket_price=5000,
    )

    session.add(showtime)
    session.commit()

    seat = SeatInventory(
        showtime_id=showtime.id,
        seat_number="A1",
        status="available",
    )

    session.add(seat)
    session.commit()

    hold = create_hold(
        session=session,
        user_id=user.id,
        seat_inventory_id=seat.id,
    )

    assert hold.user_id == user.id
    assert hold.seat_inventory_id == seat.id
    assert hold.status == "active"
    assert hold.expires_at > datetime.utcnow()

    session.refresh(seat)

    assert seat.status == "held"


def test_booking_fails_when_hold_is_no_longer_active(session):
    user = User(
        email="inactivehold@example.com",
        password_hash=hash_password("password123"),
        full_name="Inactive Hold User",
        role="moviegoer",
    )

    film = Film(
        title="Inactive Hold Film",
        description="A test film",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Inactive Hold Screen",
        total_seats=10,
    )

    session.add(user)
    session.add(film)
    session.add(screen)
    session.commit()

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        ticket_price=5000,
    )

    session.add(showtime)
    session.commit()

    seat = SeatInventory(
        showtime_id=showtime.id,
        seat_number="A1",
        status="available",
    )

    session.add(seat)
    session.commit()

    hold = create_hold(
        session=session,
        user_id=user.id,
        seat_inventory_id=seat.id,
    )

    hold.status = "cancelled"
    session.add(hold)
    session.commit()

    with pytest.raises(ValueError, match="Hold is no longer active"):
        create_booking(
            session=session,
            user_id=user.id,
            hold_id=hold.id,
        )


def test_expired_hold_allows_another_user_to_hold_seat(session):
    user_a = User(
        email="expiredholder@example.com",
        password_hash=hash_password("password123"),
        full_name="Expired Holder",
        role="moviegoer",
    )

    user_b = User(
        email="newholder@example.com",
        password_hash=hash_password("password123"),
        full_name="New Holder",
        role="moviegoer",
    )

    film = Film(
        title="Expired Hold Film",
        description="A test film",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Expired Hold Screen",
        total_seats=10,
    )

    session.add(user_a)
    session.add(user_b)
    session.add(film)
    session.add(screen)
    session.commit()

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        ticket_price=5000,
    )

    session.add(showtime)
    session.commit()

    seat = SeatInventory(
        showtime_id=showtime.id,
        seat_number="A1",
        status="available",
    )

    session.add(seat)
    session.commit()

    first_hold = create_hold(
        session=session,
        user_id=user_a.id,
        seat_inventory_id=seat.id,
    )

    first_hold.expires_at = datetime.utcnow() - timedelta(minutes=1)
    session.add(first_hold)
    session.commit()

    second_hold = create_hold(
        session=session,
        user_id=user_b.id,
        seat_inventory_id=seat.id,
    )

    assert first_hold.status == "expired"
    assert second_hold.status == "active"
    assert second_hold.user_id == user_b.id

    session.refresh(seat)

    assert seat.status == "held"


def test_cannot_hold_nonexistent_seat(session):
    user = User(
        email="missingseat@example.com",
        password_hash=hash_password("password123"),
        full_name="Missing Seat User",
        role="moviegoer",
    )

    session.add(user)
    session.commit()

    with pytest.raises(ValueError, match="Seat not found"):
        create_hold(
            session=session,
            user_id=user.id,
            seat_inventory_id=999999,
        )


def test_api_user_can_create_hold(client, session):
    user = User(
        email="apiuser@example.com",
        password_hash=hash_password("password123"),
        full_name="API User",
        role="moviegoer",
    )

    film = Film(
        title="API Test Film",
        description="Film for API testing",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="API Screen",
        total_seats=10,
    )

    session.add(user)
    session.add(film)
    session.add(screen)
    session.commit()

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        ticket_price=5000,
    )

    session.add(showtime)
    session.commit()

    seat = SeatInventory(
        showtime_id=showtime.id,
        seat_number="A1",
        status="available",
    )

    session.add(seat)
    session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "apiuser@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/holds",
        json={
            "seat_inventory_id": seat.id,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["seat_inventory_id"] == seat.id
    assert data["user_id"] == user.id
    assert data["status"] == "active"
    assert data["expires_at"] is not None


def test_api_cannot_hold_already_held_seat(client, session):
    user = User(
        email="heldseat@example.com",
        password_hash=hash_password("password123"),
        full_name="Held Seat User",
        role="moviegoer",
    )

    film = Film(
        title="Held Seat Film",
        description="Film for API testing",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Held Seat Screen",
        total_seats=10,
    )

    session.add(user)
    session.add(film)
    session.add(screen)
    session.commit()

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        ticket_price=5000,
    )

    session.add(showtime)
    session.commit()

    seat = SeatInventory(
        showtime_id=showtime.id,
        seat_number="A1",
        status="available",
    )

    session.add(seat)
    session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "heldseat@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}",
    }

    first_response = client.post(
        "/api/v1/holds",
        json={"seat_inventory_id": seat.id},
        headers=headers,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/holds",
        json={"seat_inventory_id": seat.id},
        headers=headers,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Seat is currently held"


def test_api_cannot_hold_nonexistent_seat(client, session):
    user = User(
        email="missingseat@example.com",
        password_hash=hash_password("password123"),
        full_name="Missing Seat User",
        role="moviegoer",
    )

    session.add(user)
    session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "missingseat@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/holds",
        json={
            "seat_inventory_id": 999999,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Seat not found"