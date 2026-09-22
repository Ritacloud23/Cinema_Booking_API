from datetime import datetime

from sqlmodel import Session, select

from app.db.models.film import Film
from app.db.models.price_rule import PriceRule


def get_film_price(
    session: Session,
    film_id: int,
    showtime_start: datetime,
) -> float:
    film = session.exec(
        select(Film).where(Film.id == film_id)
    ).first()

    if film is None:
        raise ValueError("Film not found")

    rules = session.exec(
        select(PriceRule)
        .where(
            PriceRule.film_id == film_id,
            PriceRule.active == True,
            PriceRule.starts_at <= showtime_start,
            PriceRule.ends_at >= showtime_start,
        )
        .order_by(PriceRule.priority.desc())
    ).all()

    if rules:
        return rules[0].price

    return film.base_price