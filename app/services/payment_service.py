import uuid

from sqlmodel import Session, select

from app.db.models.booking import Booking
from app.db.models.payment import Payment


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