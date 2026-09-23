from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select

from app.cache.redis import redis_client
from app.db.models.hold import Hold
from app.db.models.seat_inventory import SeatInventory
from app.db.session import engine
from app.firestore.live_board import publish_showtime_board


def expire_holds(session: Session):
    now = datetime.utcnow()

    expired_holds = session.exec(
        select(Hold).where(
            Hold.status == "active",
            Hold.expires_at <= now,
        )
    ).all()

    expired_showtimes = set()

    for hold in expired_holds:
        seat = session.exec(
            select(SeatInventory).where(
                SeatInventory.id == hold.seat_inventory_id
            )
        ).first()

        hold.status = "expired"
        session.add(hold)

        if seat:
            seat.status = "available"
            session.add(seat)

            expired_showtimes.add(seat.showtime_id)

    session.commit()

    for showtime_id in expired_showtimes:
        redis_client.delete(
            f"seatmap:{showtime_id}"
        )

        publish_showtime_board(
            session,
            showtime_id,
        )

    return len(expired_holds)


def run_expire_holds_job():
    with Session(engine) as session:
        expired_count = expire_holds(session)

    print(
        f"Hold expiry job completed. "
        f"Expired holds: {expired_count}"
    )


scheduler = BackgroundScheduler()


def start_scheduler():
    scheduler.add_job(
        run_expire_holds_job,
        "interval",
        minutes=1,
        id="expire_holds",
        replace_existing=True,
    )

    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()