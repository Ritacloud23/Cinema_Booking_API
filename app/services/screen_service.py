from sqlmodel import Session, select

from app.db.models.screen import Screen


def create_screen(
    session: Session,
    name: str,
    total_seats: int,
):
    existing_screen = session.exec(
        select(Screen).where(
            Screen.name == name
        )
    ).first()

    if existing_screen:
        raise ValueError(
            "Screen with this name already exists"
        )

    if total_seats <= 0:
        raise ValueError(
            "Total seats must be greater than zero"
        )

    screen = Screen(
        name=name,
        total_seats=total_seats,
    )

    session.add(screen)
    session.commit()
    session.refresh(screen)

    return screen


def get_screens(
    session: Session,
):
    return list(
        session.exec(
            select(Screen)
        ).all()
    )