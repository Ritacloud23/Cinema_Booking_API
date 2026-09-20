from sqlmodel import Session, select

from app.db.models.payment import Payment
from app.db.models.processed_event import ProcessedEvent


def process_payment_webhook(
    session: Session,
    event_id: str,
    event_type: str,
    reference: str,
    amount: float,
    currency: str,
):
    existing_event = session.exec(
        select(ProcessedEvent)
        .where(
            ProcessedEvent.event_id == event_id
        )
    ).first()

    if existing_event:
        return "duplicate"

    payment = session.exec(
        select(Payment)
        .where(
            Payment.reference == reference
        )
        .with_for_update()
    ).first()

    if payment is None:
        session.add(
            ProcessedEvent(
                event_id=event_id,
                event_type=event_type,
            )
        )

        session.commit()

        return "orphan"

    if payment.amount != amount:
        raise ValueError("Payment amount mismatch")

    if payment.currency != currency:
        raise ValueError("Payment currency mismatch")

    payment.status = "succeeded"

    session.add(
        ProcessedEvent(
            event_id=event_id,
            event_type=event_type,
        )
    )

    session.add(payment)

    session.commit()

    return "processed"