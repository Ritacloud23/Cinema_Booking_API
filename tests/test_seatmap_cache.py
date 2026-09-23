from datetime import datetime, timedelta

import pytest

from app.cache.redis import redis_client
from app.core.security import hash_password
from app.db.models.film import Film
from app.db.models.screen import Screen
from app.db.models.seat_inventory import SeatInventory
from app.db.models.showtime import Showtime
from app.db.models.user import User
from app.services.hold_service import create_hold
from app.services.seatmap_service import get_seat_map


@pytest.fixture(autouse=True)
def clear_redis():
    redis_client.flushdb()
    yield
    redis_client.flushdb()


def create_test_showtime(session):
    film = Film(
        title="Cache Test Film",
        description="Film for cache testing",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Cache Test Screen",
        total_seats=10,
    )

    session.add(film)
    session.add(screen)
    session.commit()

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        ticket_price=5000,
    )

    session.add(showtime)
    session.commit()

    return showtime


def test_seat_map_is_cached(session):
    showtime = create_test_showtime(session)

    seat = SeatInventory(
        showtime_id=showtime.id,
        seat_number="A10",
        status="available",
    )

    session.add(seat)
    session.commit()

    result = get_seat_map(
        session=session,
        showtime_id=showtime.id,
    )

    assert len(result) == 1
    assert result[0].seat_number == "A10"

    cached = redis_client.get(
        f"seatmap:{showtime.id}"
    )

    assert cached is not None


def test_seat_map_cache_hit_does_not_query_database(
    session,
    monkeypatch,
):
    showtime = create_test_showtime(session)

    seat = SeatInventory(
        showtime_id=showtime.id,
        seat_number="A10",
        status="available",
    )

    session.add(seat)
    session.commit()

    first_result = get_seat_map(
        session=session,
        showtime_id=showtime.id,
    )

    assert first_result[0].status == "available"

    def database_should_not_be_called(*args, **kwargs):
        raise AssertionError(
            "Database was queried during a cache hit"
        )

    monkeypatch.setattr(
        session,
        "exec",
        database_should_not_be_called,
    )

    second_result = get_seat_map(
        session=session,
        showtime_id=showtime.id,
    )

    assert second_result[0].seat_number == "A10"
    assert second_result[0].status == "available"


def test_seat_map_cache_is_invalidated_when_seat_changes(
    session,
):
    user = User(
        email="cachehold@example.com",
        password_hash=hash_password("password123"),
        full_name="Cache Hold User",
        role="moviegoer",
    )

    showtime = create_test_showtime(session)

    seat = SeatInventory(
        showtime_id=showtime.id,
        seat_number="A10",
        status="available",
    )

    session.add(user)
    session.add(seat)
    session.commit()

    first_result = get_seat_map(
        session=session,
        showtime_id=showtime.id,
    )

    assert first_result[0].status == "available"

    cache_key = f"seatmap:{showtime.id}"

    assert redis_client.get(cache_key) is not None

    create_hold(
        session=session,
        user_id=user.id,
        seat_inventory_id=seat.id,
    )

    assert redis_client.get(cache_key) is None

    second_result = get_seat_map(
        session=session,
        showtime_id=showtime.id,
    )

    assert second_result[0].status == "held"

    assert redis_client.get(cache_key) is not None