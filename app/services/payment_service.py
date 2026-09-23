import uuid

from sqlmodel import Session, select

from app.db.models.booking import Booking
from app.db.models.booking_seat import BookingSeat
from app.db.models.payment import Payment
from app.db.models.processed_event import ProcessedEvent
from app.db.models.seat_inventory import SeatInventory
from app.cache.redis import redis_client
from app.firestore.live_board import publish_showtime_board


def create_payment(session: Session, user_id: int, booking_id: int):
    booking = session.exec(
        select(Booking).where(Booking.id == booking_id)
    ).first()

    if booking is None:
        raise ValueError("Booking not found")

    if booking.user_id != user_id:
        raise PermissionError("You do not own this booking")

    if booking.status != "pending":
        raise ValueError("Booking is not pending")

    existing_payment = session.exec(
        select(Payment).where(Payment.booking_id == booking_id)
    ).first()

    if existing_payment:
        return existing_payment

    payment = Payment(
        booking_id=booking.id,
        reference=f"PAY-{uuid.uuid4().hex[:12].upper()}",
        amount=booking.total_amount,
        currency="NGN",
        status="pending",
    )

    session.add(payment)
    session.commit()
    session.refresh(payment)

    return payment


def process_payment_webhook(
    session: Session,
    event_id: str,
    event_type: str,
    reference: str,
):
    existing_event = session.exec(
        select(ProcessedEvent).where(
            ProcessedEvent.event_id == event_id
        )
    ).first()

    if existing_event:
        return {"message": "Event already processed"}

    payment = session.exec(
        select(Payment).where(
            Payment.reference == reference
        )
    ).first()

    if payment is None:
        event = ProcessedEvent(
            event_id=event_id,
            event_type=event_type,
        )
        session.add(event)
        session.commit()

        return {"message": "Payment reference not found"}

    if event_type == "payment.succeeded":
        payment.status = "success"

        booking = session.exec(
            select(Booking).where(
                Booking.id == payment.booking_id
            )
        ).first()

        if booking:
            booking.status = "confirmed"

            booking_seats = session.exec(
                select(BookingSeat).where(
                    BookingSeat.booking_id == booking.id
                )
            ).all()

            for booking_seat in booking_seats:
                seat = session.exec(
                    select(SeatInventory).where(
                        SeatInventory.id == booking_seat.seat_inventory_id
                    )
                ).first()

                if seat:
                    seat.status = "booked"
                    session.add(seat)

            session.add(booking)

        session.add(payment)

    event = ProcessedEvent(
        event_id=event_id,
        event_type=event_type,
    )

    session.add(event)

    # PostgreSQL must be updated first.
    session.commit()

    # Invalidate the cached seat map after the booking is committed.
    if event_type == "payment.succeeded" and booking:
        redis_client.delete(
            f"seatmap:{booking.showtime_id}"
        )

        publish_showtime_board(
            session,
            booking.showtime_id,
        )

    return {"message": "Webhook processed"}