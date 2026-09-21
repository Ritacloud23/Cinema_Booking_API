from datetime import datetime, timedelta
from sqlmodel import Session,select

from app.db.models.hold import Hold
from app.db.models.seat_inventory import SeatInventory


HOLD_DURATION_MINUTES = 10


def create_hold(
    session: Session,
    user_id: int,
    seat_inventory_id: int,
) -> Hold:
    seat = session.exec(
        select(SeatInventory)
        .where(SeatInventory.id == seat_inventory_id)
        .with_for_update()
    ).first()

    if seat is None:
        raise ValueError("Seat not found")

    now = datetime.utcnow()

    existing_hold = session.exec(
        select(Hold)
        .where(
            Hold.seat_inventory_id == seat_inventory_id,
            Hold.status == "active",
        )
    ).first()

    if existing_hold:
        if existing_hold.expires_at > now:
            raise ValueError("Seat is currently held")

        existing_hold.status = "expired"
        session.add(existing_hold)

    if seat.status != "available":
        raise ValueError("Seat is not available")

    expires_at = now + timedelta(
        minutes=HOLD_DURATION_MINUTES
    )

    hold = Hold(
        user_id=user_id,
        seat_inventory_id=seat_inventory_id,
        status="active",
        expires_at=expires_at,
    )

    seat.status = "held"

    session.add(hold)
    session.add(seat)

    session.commit()
    session.refresh(hold)

    return hold