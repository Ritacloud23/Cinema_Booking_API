from datetime import datetime, timedelta

from app.db.models.film import Film
from app.db.models.price_rule import PriceRule
from app.db.models.screen import Screen
from app.db.models.showtime import Showtime
from app.services.pricing_service import get_film_price


def test_film_base_price_is_used_when_no_rule_applies(session):
    film = Film(
        title="Base Price Film",
        description="Testing base pricing",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Pricing Screen",
        total_seats=10,
    )

    session.add(film)
    session.add(screen)
    session.commit()

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime(2026, 9, 22, 20, 0),
        end_time=datetime(2026, 9, 22, 22, 0),
        ticket_price=5000,
    )

    session.add(showtime)
    session.commit()

    price = get_film_price(
        session=session,
        film_id=film.id,
        showtime_start=showtime.start_time,
    )

    assert price == 5000


def test_active_price_rule_overrides_base_price(session):
    film = Film(
        title="Promo Film",
        description="Testing promo pricing",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Promo Screen",
        total_seats=10,
    )

    session.add(film)
    session.add(screen)
    session.commit()

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime(2026, 9, 27, 19, 0),
        end_time=datetime(2026, 9, 27, 21, 0),
        ticket_price=5000,
    )

    session.add(showtime)

    rule = PriceRule(
        film_id=film.id,
        name="Weekend Promo",
        price=4000,
        starts_at=datetime(2026, 9, 26, 0, 0),
        ends_at=datetime(2026, 9, 27, 23, 59),
        priority=10,
        active=True,
    )

    session.add(rule)
    session.commit()

    price = get_film_price(
        session=session,
        film_id=film.id,
        showtime_start=showtime.start_time,
    )

    assert price == 4000


def test_highest_priority_rule_wins(session):
    film = Film(
        title="Priority Film",
        description="Testing priority pricing",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Priority Screen",
        total_seats=10,
    )

    session.add(film)
    session.add(screen)
    session.commit()

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime(2026, 9, 27, 19, 0),
        end_time=datetime(2026, 9, 27, 21, 0),
        ticket_price=5000,
    )

    session.add(showtime)

    weekend_rule = PriceRule(
        film_id=film.id,
        name="Weekend Promo",
        price=4500,
        starts_at=datetime(2026, 9, 26, 0, 0),
        ends_at=datetime(2026, 9, 27, 23, 59),
        priority=10,
        active=True,
    )

    flash_sale = PriceRule(
        film_id=film.id,
        name="Flash Sale",
        price=3500,
        starts_at=datetime(2026, 9, 27, 18, 0),
        ends_at=datetime(2026, 9, 27, 21, 0),
        priority=20,
        active=True,
    )

    session.add(weekend_rule)
    session.add(flash_sale)
    session.commit()

    price = get_film_price(
        session=session,
        film_id=film.id,
        showtime_start=showtime.start_time,
    )

    assert price == 3500


def test_inactive_price_rule_is_ignored(session):
    film = Film(
        title="Inactive Rule Film",
        description="Testing inactive rules",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Inactive Rule Screen",
        total_seats=10,
    )

    session.add(film)
    session.add(screen)
    session.commit()

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime(2026, 9, 27, 19, 0),
        end_time=datetime(2026, 9, 27, 21, 0),
        ticket_price=5000,
    )

    session.add(showtime)

    rule = PriceRule(
        film_id=film.id,
        name="Disabled Promo",
        price=3000,
        starts_at=datetime(2026, 9, 27, 0, 0),
        ends_at=datetime(2026, 9, 27, 23, 59),
        priority=20,
        active=False,
    )

    session.add(rule)
    session.commit()

    price = get_film_price(
        session=session,
        film_id=film.id,
        showtime_start=showtime.start_time,
    )

    assert price == 5000