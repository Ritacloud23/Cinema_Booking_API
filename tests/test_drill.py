import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pytest
from sqlmodel import Session, select

from app.db.models.film import Film
from app.db.models.hold import Hold
from app.db.models.screen import Screen
from app.db.models.seat_inventory import SeatInventory
from app.db.models.showtime import Showtime
from app.db.models.user import User
from app.services.hold_service import create_hold
from tests.conftest import test_engine


@pytest.fixture
def disable_external_services(monkeypatch):
    monkeypatch.setattr(
        "app.services.hold_service.invalidate_seat_map",
        lambda showtime_id: None,
    )

    monkeypatch.setattr(
        "app.services.hold_service.publish_showtime_board",
        lambda session, showtime_id: None,
    )


def create_test_data(session, seat_number="A1"):
    user1 = User(
        email="user1@example.com",
        password_hash="hashed",
        full_name="User One",
        role="moviegoer",
    )

    user2 = User(
        email="user2@example.com",
        password_hash="hashed",
        full_name="User Two",
        role="moviegoer",
    )

    session.add(user1)
    session.add(user2)

    film = Film(
        title="Test Film",
        description="Test description",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    session.add(film)

    screen = Screen(
        name="Test Screen",
        total_seats=100,
    )

    session.add(screen)
    session.commit()

    session.refresh(user1)
    session.refresh(user2)
    session.refresh(film)
    session.refresh(screen)

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        ticket_price=5000,
    )

    session.add(showtime)
    session.commit()
    session.refresh(showtime)

    seat = SeatInventory(
        showtime_id=showtime.id,
        seat_number=seat_number,
        status="available",
    )

    session.add(seat)
    session.commit()
    session.refresh(seat)

    return user1, user2, seat


def attempt_hold(user_id, seat_id, barrier=None):
    with Session(test_engine) as session:
        if barrier:
            barrier.wait()

        try:
            hold = create_hold(
                session=session,
                user_id=user_id,
                seat_inventory_id=seat_id,
            )

            return {
                "success": True,
                "hold_id": hold.id,
                "error": None,
            }

        except ValueError as error:
            return {
                "success": False,
                "hold_id": None,
                "error": str(error),
            }


def test_two_users_competing_for_same_seat_only_one_wins(
    session,
    disable_external_services,
):
    user1, user2, seat = create_test_data(session)

    barrier = threading.Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                attempt_hold,
                user1.id,
                seat.id,
                barrier,
            ),
            executor.submit(
                attempt_hold,
                user2.id,
                seat.id,
                barrier,
            ),
        ]

        results = [future.result() for future in futures]

    successful = [
        result
        for result in results
        if result["success"]
    ]

    assert len(successful) == 1

    with Session(test_engine) as verify_session:
        holds = verify_session.exec(
            select(Hold).where(
                Hold.seat_inventory_id == seat.id
            )
        ).all()

        assert len(holds) == 1
        assert holds[0].status == "active"


def test_five_users_competing_for_same_seat_only_one_wins(
    session,
    disable_external_services,
):
    users = []

    for number in range(5):
        user = User(
            email=f"user{number}@example.com",
            password_hash="hashed",
            full_name=f"User {number}",
            role="moviegoer",
        )

        session.add(user)
        users.append(user)

    film = Film(
        title="Five User Film",
        description="Test description",
        duration_minutes=120,
        rating="PG",
        base_price=5000,
    )

    screen = Screen(
        name="Five User Screen",
        total_seats=100,
    )

    session.add(film)
    session.add(screen)
    session.commit()

    for user in users:
        session.refresh(user)

    session.refresh(film)
    session.refresh(screen)

    showtime = Showtime(
        film_id=film.id,
        screen_id=screen.id,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        ticket_price=5000,
    )

    session.add(showtime)
    session.commit()
    session.refresh(showtime)

    seat = SeatInventory(
        showtime_id=showtime.id,
        seat_number="B1",
        status="available",
    )

    session.add(seat)
    session.commit()
    session.refresh(seat)

    barrier = threading.Barrier(5)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(
                attempt_hold,
                user.id,
                seat.id,
                barrier,
            )
            for user in users
        ]

        results = [future.result() for future in futures]

    successful = [
        result
        for result in results
        if result["success"]
    ]

    assert len(successful) == 1


def test_losing_requests_receive_seat_held_conflict(
    session,
    disable_external_services,
):
    user1, user2, seat = create_test_data(session)

    barrier = threading.Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                attempt_hold,
                user1.id,
                seat.id,
                barrier,
            ),
            executor.submit(
                attempt_hold,
                user2.id,
                seat.id,
                barrier,
            ),
        ]

        results = [future.result() for future in futures]

    failures = [
        result
        for result in results
        if not result["success"]
    ]

    assert len(failures) == 1
    assert failures[0]["error"] == "Seat is currently held"


def test_different_seats_can_be_held_concurrently(
    session,
    disable_external_services,
):
    user1, user2, seat1 = create_test_data(
        session,
        seat_number="C1",
    )

    seat2 = SeatInventory(
        showtime_id=seat1.showtime_id,
        seat_number="C2",
        status="available",
    )

    session.add(seat2)
    session.commit()
    session.refresh(seat2)

    barrier = threading.Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                attempt_hold,
                user1.id,
                seat1.id,
                barrier,
            ),
            executor.submit(
                attempt_hold,
                user2.id,
                seat2.id,
                barrier,
            ),
        ]

        results = [future.result() for future in futures]

    successful = [
        result
        for result in results
        if result["success"]
    ]

    assert len(successful) == 2


def test_expired_hold_can_be_reclaimed_under_contention(
    session,
    disable_external_services,
):
    user1, user2, seat = create_test_data(session)

    expired_hold = Hold(
        user_id=user1.id,
        seat_inventory_id=seat.id,
        status="active",
        expires_at=datetime.utcnow() - timedelta(minutes=1),
    )

    seat.status = "held"

    session.add(expired_hold)
    session.add(seat)
    session.commit()

    barrier = threading.Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                attempt_hold,
                user1.id,
                seat.id,
                barrier,
            ),
            executor.submit(
                attempt_hold,
                user2.id,
                seat.id,
                barrier,
            ),
        ]

        results = [future.result() for future in futures]

    successful = [
        result
        for result in results
        if result["success"]
    ]

    assert len(successful) == 1

    with Session(test_engine) as verify_session:
        holds = verify_session.exec(
            select(Hold).where(
                Hold.seat_inventory_id == seat.id
            )
        ).all()

        active_holds = [
            hold
            for hold in holds
            if hold.status == "active"
        ]

        expired_holds = [
            hold
            for hold in holds
            if hold.status == "expired"
        ]

        assert len(active_holds) == 1
        assert len(expired_holds) == 1


        