from datetime import datetime, timezone

from sqlmodel import Session, select

from app.db.models.film import Film
from app.db.models.screen import Screen
from app.db.models.seat_inventory import SeatInventory
from app.db.models.showtime import Showtime
from app.firestore.client import db


COLLECTION_NAME = "live_showtimes"


def publish_showtime_board(session: Session, showtime_id: int):
    showtime = session.exec(
        select(Showtime).where(Showtime.id == showtime_id)
    ).first()

    if showtime is None:
        raise ValueError("Showtime not found")

    film = session.exec(
        select(Film).where(Film.id == showtime.film_id)
    ).first()

    screen = session.exec(
        select(Screen).where(Screen.id == showtime.screen_id)
    ).first()

    seats = session.exec(
        select(SeatInventory).where(
            SeatInventory.showtime_id == showtime_id
        )
    ).all()

    available_seats = sum(
        1 for seat in seats if seat.status == "available"
    )

    held_seats = sum(
        1 for seat in seats if seat.status == "held"
    )

    booked_seats = sum(
        1 for seat in seats if seat.status == "booked"
    )

    data = {
        "showtime_id": showtime.id,
        "film_title": film.title if film else None,
        "screen_name": screen.name if screen else None,
        "start_time": showtime.start_time.isoformat(),
        "available_seats": available_seats,
        "held_seats": held_seats,
        "booked_seats": booked_seats,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    db.collection(COLLECTION_NAME).document(
        f"showtime_{showtime_id}"
    ).set(data)

    return data

def get_showtime_board(showtime_id: int):
    document = (
        db.collection(COLLECTION_NAME)
        .document(f"showtime_{showtime_id}")
        .get()
    )

    if not document.exists:
        return None

    return document.to_dict()