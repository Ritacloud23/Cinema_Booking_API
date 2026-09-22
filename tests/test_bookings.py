from datetime import datetime, timedelta

import pytest

from app.core.security import hash_password
from app.db.models.booking import Booking
from app.db.models.film import Film
from app.db.models.screen import Screen
from app.db.models.seat_inventory import SeatInventory
from app.db.models.showtime import Showtime
from app.db.models.user import User
from app.services.booking_service import create_booking
from app.services.hold_service import create_hold
from app.db.models.price_rule import PriceRule


def test_user_can_create_booking_from_hold(session):
    user = User(
        email="testuser@example.com",
        password_hash=hash_password("password123"),
        full_name="Test User",
        role="moviegoer",
    )

    film = Film(
        title="Test Film",
        description="A test film",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Test Screen",
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

    booking = create_booking(
        session=session,
        user_id=user.id,
        hold_id=hold.id,
    )

    assert booking.user_id == user.id
    assert booking.showtime_id == showtime.id
    assert booking.status == "pending"
    assert booking.total_amount == 5000
    assert booking.reference.startswith("SH-")


def test_user_cannot_use_another_users_hold(session):
    user_a = User(
        email="usera@example.com",
        password_hash=hash_password("password123"),
        full_name="User A",
        role="moviegoer",
    )

    user_b = User(
        email="userb@example.com",
        password_hash=hash_password("password123"),
        full_name="User B",
        role="moviegoer",
    )

    film = Film(
        title="Ownership Test Film",
        description="A test film",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Ownership Test Screen",
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

    hold = create_hold(
        session=session,
        user_id=user_a.id,
        seat_inventory_id=seat.id,
    )

    with pytest.raises(PermissionError):
        create_booking(
            session=session,
            user_id=user_b.id,
            hold_id=hold.id,
        )


def test_booking_fails_when_hold_has_expired(session):
    user = User(
        email="expired@example.com",
        password_hash=hash_password("password123"),
        full_name="Expired User",
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

    hold.expires_at = datetime.utcnow() - timedelta(minutes=1)
    session.add(hold)
    session.commit()

    with pytest.raises(ValueError, match="Hold has expired"):
        create_booking(
            session=session,
            user_id=user.id,
            hold_id=hold.id,
        )

    assert hold.status == "expired"
    assert seat.status == "available"


def test_booking_fails_when_hold_does_not_exist(session):
    user = User(
        email="missinghold@example.com",
        password_hash=hash_password("password123"),
        full_name="Missing Hold User",
        role="moviegoer",
    )

    session.add(user)
    session.commit()

    with pytest.raises(ValueError, match="Hold not found"):
        create_booking(
            session=session,
            user_id=user.id,
            hold_id=999999,
        )


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


def test_booking_fails_when_seat_is_not_held(session):
    user = User(
        email="seatstatus@example.com",
        password_hash=hash_password("password123"),
        full_name="Seat Status User",
        role="moviegoer",
    )

    film = Film(
        title="Seat Status Film",
        description="A test film",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Seat Status Screen",
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

    seat.status = "available"
    session.add(seat)
    session.commit()

    with pytest.raises(ValueError, match="Seat is not held"):
        create_booking(
            session=session,
            user_id=user.id,
            hold_id=hold.id,
        )


def test_api_user_cannot_book_another_users_hold(client, session):
    user_a = User(
        email="owner@example.com",
        password_hash=hash_password("password123"),
        full_name="Hold Owner",
        role="moviegoer",
    )

    user_b = User(
        email="other@example.com",
        password_hash=hash_password("password123"),
        full_name="Other User",
        role="moviegoer",
    )

    session.add(user_a)
    session.add(user_b)

    film = Film(
        title="Ownership Test Film",
        description="Film for ownership testing",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Ownership Test Screen",
        total_seats=10,
    )

    session.add(film)
    session.add(screen)
    session.commit()

    session.refresh(user_a)
    session.refresh(user_b)
    session.refresh(film)
    session.refresh(screen)

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        ticket_price=5000,
    )

    session.add(showtime)
    session.commit()
    session.refresh(showtime)

    seat = SeatInventory(
        showtime_id=showtime.id,
        seat_number="A1",
        status="available",
    )

    session.add(seat)
    session.commit()
    session.refresh(seat)

    hold = create_hold(
        session=session,
        user_id=user_a.id,
        seat_inventory_id=seat.id,
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "other@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/bookings",
        json={
            "hold_id": hold.id,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You do not own this hold"


def test_api_user_can_create_booking_from_hold(client, session):
    user = User(
        email="bookingapi@example.com",
        password_hash=hash_password("password123"),
        full_name="Booking API User",
        role="moviegoer",
    )

    film = Film(
        title="Booking API Film",
        description="Film for booking API testing",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Booking API Screen",
        total_seats=10,
    )

    session.add(user)
    session.add(film)
    session.add(screen)
    session.commit()

    session.refresh(user)
    session.refresh(film)
    session.refresh(screen)

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        ticket_price=5000,
    )

    session.add(showtime)
    session.commit()
    session.refresh(showtime)

    seat = SeatInventory(
        showtime_id=showtime.id,
        seat_number="A1",
        status="available",
    )

    session.add(seat)
    session.commit()
    session.refresh(seat)

    hold = create_hold(
        session=session,
        user_id=user.id,
        seat_inventory_id=seat.id,
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "bookingapi@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/bookings",
        json={
            "hold_id": hold.id,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == user.id
    assert data["showtime_id"] == showtime.id
    assert data["status"] == "pending"
    assert data["total_amount"] == 5000
    assert data["reference"].startswith("SH-")


def test_api_cannot_create_booking_from_nonexistent_hold(client, session):
    user = User(
        email="missingholdapi@example.com",
        password_hash=hash_password("password123"),
        full_name="Missing Hold API User",
        role="moviegoer",
    )

    session.add(user)
    session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "missingholdapi@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/bookings",
        json={
            "hold_id": 999999,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Hold not found"


def test_api_cannot_create_booking_from_expired_hold(client, session):
    user = User(
        email="expiredapi@example.com",
        password_hash=hash_password("password123"),
        full_name="Expired API User",
        role="moviegoer",
    )

    film = Film(
        title="Expired API Film",
        description="Film for expired hold testing",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Expired API Screen",
        total_seats=10,
    )

    session.add(user)
    session.add(film)
    session.add(screen)
    session.commit()

    session.refresh(user)
    session.refresh(film)
    session.refresh(screen)

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        ticket_price=5000,
    )

    session.add(showtime)
    session.commit()
    session.refresh(showtime)

    seat = SeatInventory(
        showtime_id=showtime.id,
        seat_number="A1",
        status="available",
    )

    session.add(seat)
    session.commit()
    session.refresh(seat)

    hold = create_hold(
        session=session,
        user_id=user.id,
        seat_inventory_id=seat.id,
    )

    hold.expires_at = datetime.utcnow() - timedelta(minutes=1)
    session.add(hold)
    session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "expiredapi@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/bookings",
        json={
            "hold_id": hold.id,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Hold has expired"

def test_booking_uses_active_price_rule(session):
    user = User(
        email="pricingbooking@example.com",
        password_hash=hash_password("password123"),
        full_name="Pricing Booking User",
        role="moviegoer",
    )

    film = Film(
        title="Pricing Booking Film",
        description="Testing booking pricing",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Pricing Booking Screen",
        total_seats=10,
    )

    session.add(user)
    session.add(film)
    session.add(screen)
    session.commit()

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime(2026, 9, 27, 19, 0),
        end_time=datetime(2026, 9, 27, 21, 0),
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

    rule = PriceRule(
        film_id=film.id,
        name="Weekend Promo",
        price=4000,
        starts_at=datetime(2026, 9, 27, 0, 0),
        ends_at=datetime(2026, 9, 27, 23, 59),
        priority=10,
        active=True,
    )

    session.add(rule)
    session.commit()

    hold = create_hold(
        session=session,
        user_id=user.id,
        seat_inventory_id=seat.id,
    )

    booking = create_booking(
        session=session,
        user_id=user.id,
        hold_id=hold.id,
    )

    assert booking.total_amount == 4000