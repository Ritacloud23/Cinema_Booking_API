from datetime import datetime, timedelta

from app.db.models.booking import Booking
from app.db.models.film import Film
from app.db.models.hold import Hold
from app.db.models.screen import Screen
from app.db.models.seat_inventory import SeatInventory
from app.db.models.showtime import Showtime
from app.db.models.user import User
from app.services.booking_service import create_booking
from app.services.hold_service import create_hold
from app.core.security import hash_password


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