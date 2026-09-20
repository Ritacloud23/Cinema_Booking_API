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

    showtime = Showtime(
        film_id=film_id,
        screen_id=screen_id,
        start_time=start_time,
        end_time=end_time,
    )

    session.add(showtime)
    session.commit()
    session.refresh(showtime)

    return showtime