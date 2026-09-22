import uuid
from datetime import datetime
from app.services.pricing_service import get_film_price

from sqlmodel import Session,select

from app.db.models.booking import Booking
from app.db.models.booking_seat import BookingSeat
from app.db.models.hold import Hold
from app.db.models.seat_inventory import SeatInventory
from app.db.models.showtime import Showtime


def create_booking(
    session: Session,
    user_id: int,
    hold_id: int,
):
    # Lock the hold so two requests cannot use it at the same time.
    hold = session.exec(
        select(Hold)
        .where(Hold.id == hold_id)
        .with_for_update()
    ).first()

    if hold is None:
        raise ValueError("Hold not found")

    # Users can only create bookings from their own holds.
    if hold.user_id != user_id:
        raise PermissionError(
            "You do not own this hold"
        )

    # The hold must still be active.
    if hold.status != "active":
        raise ValueError(
            "Hold is no longer active"
        )

    # Check the actual expiry time.
    now = datetime.utcnow()

    if hold.expires_at <= now:
        seat = session.exec(
            select(SeatInventory)
            .where(
                SeatInventory.id == hold.seat_inventory_id
            )
            .with_for_update()
        ).first()

        if seat:
            seat.status = "available"

        hold.status = "expired"

        session.add(hold)

        if seat:
            session.add(seat)

        session.commit()

        raise ValueError("Hold has expired")

    # Lock the seat as well.
    seat = session.exec(
        select(SeatInventory)
        .where(
            SeatInventory.id == hold.seat_inventory_id
        )
        .with_for_update()
    ).first()

    if seat is None:
        raise ValueError("Seat not found")

    if seat.status != "held":
        raise ValueError("Seat is not held")

    showtime = session.exec(
        select(Showtime)
        .where(Showtime.id == seat.showtime_id)
    ).first()

    if showtime is None:
        raise ValueError("Showtime not found")

    # Create the booking, but DO NOT book the seat yet.
    price = get_film_price(
        session=session,
        film_id=showtime.film_id,
        showtime_start=showtime.start_time,
    )

    booking = Booking(
        user_id=user_id,
        showtime_id=seat.showtime_id,
        reference=f"SH-{uuid.uuid4().hex[:12].upper()}",
        status="pending",
        total_amount=price,
    )

    session.add(booking)
    session.flush()

    # Connect the booking to the held seat.
    booking_seat = BookingSeat(
        booking_id=booking.id,
        seat_inventory_id=seat.id,
    )

    session.add(booking_seat)

    session.commit()
    session.refresh(booking)

    return booking