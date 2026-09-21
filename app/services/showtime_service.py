from sqlmodel import Session, select

from app.db.models.film import Film
from app.db.models.screen import Screen
from app.db.models.showtime import Showtime


def create_showtime(
    session: Session,
    film_id: int,
    screen_id: int,
    start_time,
    end_time,
    ticket_price: float,
):
    film = session.exec(
        select(Film).where(Film.id == film_id)
    ).first()

    if film is None:
        raise ValueError("Film not found")

    screen = session.exec(
        select(Screen).where(Screen.id == screen_id)
    ).first()

    if screen is None:
        raise ValueError("Screen not found")

    if end_time <= start_time:
        raise ValueError("End time must be after start time")

    if ticket_price <= 0:
        raise ValueError("Ticket price must be greater than zero")

    showtime = Showtime(
        film_id=film_id,
        screen_id=screen_id,
        start_time=start_time,
        end_time=end_time,
        ticket_price=ticket_price,
    )

    session.add(showtime)
    session.commit()
    session.refresh(showtime)

    return showtime