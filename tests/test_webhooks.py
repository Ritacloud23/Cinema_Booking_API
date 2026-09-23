import hashlib
import hmac
import json

from fastapi.testclient import TestClient
from sqlmodel import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.models.booking import Booking
from app.db.models.booking_seat import BookingSeat
from app.db.models.film import Film
from app.db.models.hold import Hold
from app.db.models.payment import Payment
from app.db.models.processed_event import ProcessedEvent
from app.db.models.screen import Screen
from app.db.models.seat_inventory import SeatInventory
from app.db.models.showtime import Showtime
from app.db.models.user import User
from app.main import app
from app.db.session import get_session


client = TestClient(app)


def create_payment_setup(session):
    user = User(
        email="webhook@test.com",
        password_hash=hash_password("password123"),
        full_name="Webhook User",
        role="moviegoer",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    film = Film(
        title="Webhook Film",
        description="Test film",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )
    session.add(film)
    session.commit()
    session.refresh(film)

    screen = Screen(
        name="Webhook Screen",
        total_seats=100,
    )
    session.add(screen)
    session.commit()
    session.refresh(screen)

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time="2026-12-01T18:00:00",
        end_time="2026-12-01T20:00:00",
        ticket_price=5000,
    )
    session.add(showtime)
    session.commit()
    session.refresh(showtime)

    seat = SeatInventory(
        showtime_id=showtime.id,
        seat_number="A10",
        status="held",
    )
    session.add(seat)
    session.commit()
    session.refresh(seat)

    hold = Hold(
        user_id=user.id,
        seat_inventory_id=seat.id,
        status="active",
        expires_at="2026-12-01T17:55:00",
    )
    session.add(hold)
    session.commit()
    session.refresh(hold)

    booking = Booking(
        user_id=user.id,
        showtime_id=showtime.id,
        reference="SH-WEBHOOK123",
        status="pending",
        total_amount=5000,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)

    booking_seat = BookingSeat(
        booking_id=booking.id,
        seat_inventory_id=seat.id,
    )
    session.add(booking_seat)

    payment = Payment(
        booking_id=booking.id,
        reference="PAY-WEBHOOK123",
        amount=5000,
        currency="NGN",
        status="pending",
    )
    session.add(payment)

    session.commit()
    session.refresh(payment)

    return user, booking, seat, payment


def sign_payload(payload):
    raw_body = json.dumps(payload).encode()

    signature = hmac.new(
        settings.PAYSTACK_SECRET.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return raw_body, signature


def test_successful_payment_webhook(client, session):
    user, booking, seat, payment = create_payment_setup(session)

    payload = {
        "event_id": "evt_success_001",
        "type": "payment.succeeded",
        "reference": payment.reference,
        "amount": payment.amount,
        "currency": payment.currency,
    }

    raw_body, signature = sign_payload(payload)

    response = client.post(
        "/api/v1/webhooks/payment",
        content=raw_body,
        headers={"X-Signature": signature},
    )

    assert response.status_code == 200

    session.refresh(payment)
    session.refresh(booking)
    session.refresh(seat)

    assert payment.status == "success"
    assert booking.status == "confirmed"
    assert seat.status == "booked"

    event = session.exec(
        select(ProcessedEvent).where(
            ProcessedEvent.event_id == "evt_success_001"
        )
    ).first()

    assert event is not None


def test_webhook_rejects_bad_signature(client, session):
    _, _, _, payment = create_payment_setup(session)

    payload = {
        "event_id": "evt_bad_signature",
        "type": "payment.succeeded",
        "reference": payment.reference,
        "amount": payment.amount,
        "currency": payment.currency,
    }

    raw_body = json.dumps(payload).encode()

    response = client.post(
        "/api/v1/webhooks/payment",
        content=raw_body,
        headers={"X-Signature": "wrong-signature"},
    )

    assert response.status_code == 401


def test_duplicate_webhook_is_idempotent(client, session):
    _, booking, seat, payment = create_payment_setup(session)

    payload = {
        "event_id": "evt_duplicate_001",
        "type": "payment.succeeded",
        "reference": payment.reference,
        "amount": payment.amount,
        "currency": payment.currency,
    }

    raw_body, signature = sign_payload(payload)

    first_response = client.post(
        "/api/v1/webhooks/payment",
        content=raw_body,
        headers={"X-Signature": signature},
    )

    second_response = client.post(
        "/api/v1/webhooks/payment",
        content=raw_body,
        headers={"X-Signature": signature},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    session.refresh(payment)
    session.refresh(booking)
    session.refresh(seat)

    assert payment.status == "success"
    assert booking.status == "confirmed"
    assert seat.status == "booked"

    events = session.exec(
        select(ProcessedEvent).where(
            ProcessedEvent.event_id == "evt_duplicate_001"
        )
    ).all()

    assert len(events) == 1


def test_orphan_payment_reference_is_recorded(client, session):
    payload = {
        "event_id": "evt_orphan_001",
        "type": "payment.succeeded",
        "reference": "PAY-DOES-NOT-EXIST",
        "amount": 5000,
        "currency": "NGN",
    }

    raw_body, signature = sign_payload(payload)

    response = client.post(
        "/api/v1/webhooks/payment",
        content=raw_body,
        headers={"X-Signature": signature},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Payment reference not found"

    event = session.exec(
        select(ProcessedEvent).where(
            ProcessedEvent.event_id == "evt_orphan_001"
        )
    ).first()

    assert event is not None


def test_webhook_requires_signature(client, session):
    payload = {
        "event_id": "evt_missing_signature",
        "type": "payment.succeeded",
        "reference": "PAY-123",
        "amount": 5000,
        "currency": "NGN",
    }

    response = client.post(
        "/api/v1/webhooks/payment",
        json=payload,
    )

    assert response.status_code == 401