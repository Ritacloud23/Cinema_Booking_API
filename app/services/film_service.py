from sqlmodel import Session, select

from app.db.models.film import Film


def create_film(
    session: Session,
    title: str,
    description: str,
    duration_minutes: int,
    rating: str,
    base_price: float,
) -> Film:
    if base_price <= 0:
        raise ValueError("Base price must be greater than zero")

    film = Film(
        title=title,
        description=description,
        duration_minutes=duration_minutes,
        rating=rating,
        base_price=base_price,
    )

    session.add(film)
    session.commit()
    session.refresh(film)

    return film


def get_films(session: Session) -> list[Film]:
    return list(
        session.exec(
            select(Film)
        ).all()
    )