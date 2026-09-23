import json

from sqlmodel import Session, select

from app.cache.redis import redis_client
from app.db.models.screen import Screen
from app.db.models.seat_inventory import SeatInventory
from app.db.models.showtime import Showtime
from app.schemas.seat_inventory import SeatResponse


def generate_seats(
    session: Session,
    showtime_id: int,
):
    showtime = session.exec(
        select(Showtime).where(
            Showtime.id == showtime_id
        )
    ).first()

    if showtime is None:
        raise ValueError("Showtime not found")

    screen = session.exec(
        select(Screen).where(
            Screen.id == showtime.screen_id
        )
    ).first()

    if screen is None:
        raise ValueError("Screen not found")

    existing_seats = session.exec(
        select(SeatInventory).where(
            SeatInventory.showtime_id == showtime_id
        )
    ).all()

    if existing_seats:
        return list(existing_seats)

    seats = []

    seats_per_row = 10

    for number in range(1, screen.total_seats + 1):
        row_number = ((number - 1) // seats_per_row) + 1
        seat_position = ((number - 1) % seats_per_row) + 1

        seat = SeatInventory(
            showtime_id=showtime_id,
            seat_number=f"{chr(64 + row_number)}{seat_position}",
            status="available",
        )

        seats.append(seat)

    session.add_all(seats)
    session.commit()

    for seat in seats:
        session.refresh(seat)

    return seats


def get_seat_map(
    session: Session,
    showtime_id: int,
):
    cache_key = f"seatmap:{showtime_id}"

    cached_seats = redis_client.get(cache_key)

    if cached_seats:
        seats = json.loads(cached_seats)

        return [
            SeatResponse.model_validate(seat)
            for seat in seats
        ]

    seats = list(
        session.exec(
            select(SeatInventory)
            .where(
                SeatInventory.showtime_id == showtime_id
            )
            .order_by(SeatInventory.seat_number)
        ).all()
    )

    response = [
        SeatResponse.model_validate(
            seat,
            from_attributes=True,
        ).model_dump()
        for seat in seats
    ]

    redis_client.set(
        cache_key,
        json.dumps(response),
        ex=300,
    )

    return [
        SeatResponse.model_validate(seat)
        for seat in response
    ]


def invalidate_seat_map(showtime_id: int):
    cache_key = f"seatmap:{showtime_id}"
    redis_client.delete(cache_key)