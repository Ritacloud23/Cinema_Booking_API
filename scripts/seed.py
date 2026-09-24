import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.core.security import hash_password
from app.db.models import Film, PriceRule, Screen, Showtime, User
from app.db.session import engine
from app.services.seatmap_service import generate_seats


def seed():
    with Session(engine) as session:

        # ---------------------------------------------------------
        # 1. USERS
        # ---------------------------------------------------------

        users = [
            {
                "email": "moviegoer@screenhive.com",
                "password": "password123",
                "full_name": "Demo Moviegoer",
                "role": "moviegoer",
            },
            {
                "email": "cashier@screenhive.com",
                "password": "password123",
                "full_name": "Demo Cashier",
                "role": "cashier",
            },
            {
                "email": "manager@screenhive.com",
                "password": "password123",
                "full_name": "Demo Manager",
                "role": "manager",
            },
        ]

        for user_data in users:
            existing_user = session.exec(
                select(User).where(User.email == user_data["email"])
            ).first()

            if existing_user is None:
                user = User(
                    email=user_data["email"],
                    password_hash=hash_password(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                )

                session.add(user)

        session.commit()

        # ---------------------------------------------------------
        # 2. FILMS
        # ---------------------------------------------------------

        films_data = [
            {
                "title": "The Last Horizon",
                "description": "A science fiction adventure across distant worlds.",
                "duration_minutes": 130,
                "rating": "PG-13",
                "base_price": 5000,
            },
            {
                "title": "City of Dreams",
                "description": "A drama about ambition, friendship, and second chances.",
                "duration_minutes": 115,
                "rating": "PG",
                "base_price": 4500,
            },
        ]

        films = []

        for film_data in films_data:
            film = session.exec(
                select(Film).where(Film.title == film_data["title"])
            ).first()

            if film is None:
                film = Film(**film_data)
                session.add(film)
                session.commit()
                session.refresh(film)

            films.append(film)

        # ---------------------------------------------------------
        # 3. SCREENS
        # ---------------------------------------------------------

        screens_data = [
            {
                "name": "Screen 1",
                "total_seats": 50,
            },
            {
                "name": "Screen 2",
                "total_seats": 40,
            },
        ]

        screens = []

        for screen_data in screens_data:
            screen = session.exec(
                select(Screen).where(Screen.name == screen_data["name"])
            ).first()

            if screen is None:
                screen = Screen(**screen_data)
                session.add(screen)
                session.commit()
                session.refresh(screen)

            screens.append(screen)

        # ---------------------------------------------------------
        # 4. SHOWTIMES
        # ---------------------------------------------------------
        # Use fixed times for the current day.
        # This makes the seed script safe to run repeatedly on
        # the same day without creating duplicate showtimes.

        seed_date = datetime.utcnow().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        showtimes_data = [
            {
                "film_id": films[0].id,
                "screen_id": screens[0].id,
                "start_time": seed_date + timedelta(hours=18),
                "end_time": seed_date + timedelta(hours=20, minutes=10),
                "ticket_price": films[0].base_price,
            },
            {
                "film_id": films[1].id,
                "screen_id": screens[1].id,
                "start_time": seed_date + timedelta(hours=21),
                "end_time": seed_date + timedelta(hours=22, minutes=55),
                "ticket_price": films[1].base_price,
            },
        ]

        showtimes = []

        for showtime_data in showtimes_data:
            showtime = session.exec(
                select(Showtime).where(
                    Showtime.film_id == showtime_data["film_id"],
                    Showtime.screen_id == showtime_data["screen_id"],
                    Showtime.start_time == showtime_data["start_time"],
                )
            ).first()

            if showtime is None:
                showtime = Showtime(**showtime_data)
                session.add(showtime)
                session.commit()
                session.refresh(showtime)

            showtimes.append(showtime)

        # ---------------------------------------------------------
        # 5. SEATS
        # ---------------------------------------------------------

        for showtime in showtimes:
            generate_seats(
                session=session,
                showtime_id=showtime.id,
            )

        # ---------------------------------------------------------
        # 6. PRICE RULE
        # ---------------------------------------------------------

        price_rule = session.exec(
            select(PriceRule).where(
                PriceRule.film_id == films[0].id,
                PriceRule.name == "Opening Special",
            )
        ).first()

        if price_rule is None:
            price_rule = PriceRule(
                film_id=films[0].id,
                name="Opening Special",
                price=6000,
                starts_at=seed_date,
                ends_at=seed_date + timedelta(days=30),
                priority=10,
                active=True,
            )

            session.add(price_rule)
            session.commit()

        print("ScreenHive seed completed successfully.")


if __name__ == "__main__":
    seed()