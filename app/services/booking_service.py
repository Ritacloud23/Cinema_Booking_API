import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlmodel import Session

from app.db.models.booking import Booking
from app.db.models.booking_seat import BookingSeat
from app.db.models.hold import Hold
from app.db.models.seat_inventory import SeatInventory


def create_booking(
    session: Session,
    user_id: int,
    hold_id: int,
) -> Booking:
    hold = session.exec(
        select(Hold)
        .where(Hold.id == hold_id)
        .with_for_update()
    ).first()

    if hold is None:
        raise ValueError("Hold not found")

    if hold.user_id != user_id:
        raise PermissionError("You do not own this hold")

    if hold.status != "active":
        raise ValueError("Hold is no longer active")

    now = datetime.now(timezone.utc)

    if hold.expires_at <= now:
        hold.status = "expired"

        seat = session.exec(
            select(SeatInventory)
            .where(
                SeatInventory.id == hold.seat_inventory_id
            )
        ).first()

        if seat:
            seat.status = "available"

        session.commit()

        raise ValueError("Hold has expired")

    seat = session.exec(
        select(SeatInventory)
        .where(
            SeatInventory.id == hold.seat_inventory_id
        )
    ).first()

    if seat is None:
        raise ValueError("Seat not found")

    if seat.status != "held":
        raise ValueError("Seat is not held")

    showtime_id = seat.showtime_id

    booking = Booking(
        user_id=user_id,
        showtime_id=showtime_id,
        reference=f"SH-{uuid.uuid4().hex[:12].upper()}",
        status="pending",
        total_amount=0.0,
    )

    session.add(booking)
    session.flush()

    booking_seat = BookingSeat(
        booking_id=booking.id,
        seat_inventory_id=seat.id,
    )

    session.add(booking_seat)

    hold.status = "paid"
    seat.status = "booked"

    session.add(hold)
    session.add(seat)

    session.commit()
    session.refresh(booking)

    return booking