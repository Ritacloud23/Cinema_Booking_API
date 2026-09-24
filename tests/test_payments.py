from datetime import datetime, timedelta

import pytest

from app.cache.redis import redis_client
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.models.booking import Booking
from app.db.models.film import Film
from app.db.models.payment import Payment
from app.db.models.screen import Screen
from app.db.models.seat_inventory import SeatInventory
from app.db.models.showtime import Showtime
from app.db.models.user import User
from app.firestore.live_board import get_showtime_board
from app.services.booking_service import create_booking
from app.services.hold_service import create_hold
from app.services.payment_service import create_payment, process_payment_webhook
from app.services.seatmap_service import get_seat_map


def create_booking_setup(session):
    user = User(
        email="paymentuser@example.com",
        password_hash=hash_password("password123"),
        full_name="Payment User",
        role="moviegoer",
    )

    film = Film(
        title="Payment Test Film",
        description="Film for payment testing",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Payment Test Screen",
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

    return user, booking


def test_user_can_create_payment(session):
    user, booking = create_booking_setup(session)

    payment = create_payment(
        session=session,
        user_id=user.id,
        booking_id=booking.id,
    )

    assert payment.id is not None
    assert payment.booking_id == booking.id
    assert payment.amount == booking.total_amount
    assert payment.currency == "NGN"
    assert payment.status == "pending"
    assert payment.reference.startswith("PAY-")


def test_payment_amount_comes_from_booking(session):
    user, booking = create_booking_setup(session)

    booking.total_amount = 4000
    session.add(booking)
    session.commit()

    payment = create_payment(
        session=session,
        user_id=user.id,
        booking_id=booking.id,
    )

    assert payment.amount == 4000


def test_user_cannot_create_payment_for_another_users_booking(session):
    user, booking = create_booking_setup(session)

    another_user = User(
        email="anotherpaymentuser@example.com",
        password_hash=hash_password("password123"),
        full_name="Another Payment User",
        role="moviegoer",
    )

    session.add(another_user)
    session.commit()

    with pytest.raises(
        PermissionError,
        match="You do not own this booking",
    ):
        create_payment(
            session=session,
            user_id=another_user.id,
            booking_id=booking.id,
        )


def test_payment_fails_for_nonexistent_booking(session):
    user = User(
        email="missingbooking@example.com",
        password_hash=hash_password("password123"),
        full_name="Missing Booking User",
        role="moviegoer",
    )

    session.add(user)
    session.commit()

    with pytest.raises(ValueError, match="Booking not found"):
        create_payment(
            session=session,
            user_id=user.id,
            booking_id=999999,
        )


def test_payment_fails_for_non_pending_booking(session):
    user, booking = create_booking_setup(session)

    booking.status = "confirmed"
    session.add(booking)
    session.commit()

    with pytest.raises(ValueError, match="Booking is not pending"):
        create_payment(
            session=session,
            user_id=user.id,
            booking_id=booking.id,
        )


def test_duplicate_payment_returns_existing_payment(session):
    user, booking = create_booking_setup(session)

    first_payment = create_payment(
        session=session,
        user_id=user.id,
        booking_id=booking.id,
    )

    second_payment = create_payment(
        session=session,
        user_id=user.id,
        booking_id=booking.id,
    )

    assert second_payment.id == first_payment.id
    assert second_payment.reference == first_payment.reference

    payments = session.query(Payment).filter(
        Payment.booking_id == booking.id
    ).all()

    assert len(payments) == 1

def test_successful_payment_invalidates_seat_map_cache(session):
    user, booking = create_booking_setup(session)

    payment = create_payment(
        session=session,
        user_id=user.id,
        booking_id=booking.id,
    )

    # Build the seat-map cache before payment succeeds.
    seat_map = get_seat_map(
        session=session,
        showtime_id=booking.showtime_id,
    )

    assert seat_map[0].status == "held"

    cache_key = f"seatmap:{booking.showtime_id}"

    assert redis_client.get(cache_key) is not None

    process_payment_webhook(
        session=session,
        event_id="payment-cache-test-001",
        event_type="payment.succeeded",
        reference=payment.reference,
    )

    # Successful payment should invalidate the stale cache.
    assert redis_client.get(cache_key) is None

    # The next read should come from PostgreSQL and show the new state.
    fresh_seat_map = get_seat_map(
        session=session,
        showtime_id=booking.showtime_id,
    )

    assert fresh_seat_map[0].status == "booked"


@pytest.mark.skipif(
    not settings.FIRESTORE_ENABLED,
    reason="Firestore is disabled in CI",
)
def test_successful_payment_updates_live_board(session):
    user, booking = create_booking_setup(session)

    payment = create_payment(
        session=session,
        user_id=user.id,
        booking_id=booking.id,
    )

    process_payment_webhook(
        session=session,
        event_id="payment-firestore-test-001",
        event_type="payment.succeeded",
        reference=payment.reference,
    )

    board = get_showtime_board(
        booking.showtime_id,
    )

    assert board["booked_seats"] == 1
    assert board["held_seats"] == 0

def test_api_payment_fails_for_non_pending_booking(
    client,
    session,
):
    user, booking = create_booking_setup(session)

    booking.status = "confirmed"
    session.add(booking)
    session.commit()

    response = client.post(
        f"/api/v1/payments?booking_id={booking.id}",
        headers={
            "Authorization": "Bearer "
            + create_access_token(user.id, user.role)
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Booking is not pending"