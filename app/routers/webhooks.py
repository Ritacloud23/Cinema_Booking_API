import hashlib
import hmac
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlmodel import Session

from app.core.config import settings
from app.db.session import get_session
from app.services.payment_service import process_payment_webhook


router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Webhooks"],
)


@router.post("/payment")
async def payment_webhook(
    request: Request,
    x_signature: str | None = Header(default=None),
    session: Session = Depends(get_session),
):
    raw_body = await request.body()

    if x_signature is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature",
        )

    expected_signature = hmac.new(
        settings.PAYSTACK_SECRET.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        expected_signature,
        x_signature,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON",
        )

    event_id = payload.get("event_id")
    event_type = payload.get("type")
    reference = payload.get("reference")

    if not event_id or not event_type or not reference:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload",
        )

    return process_payment_webhook(
        session=session,
        event_id=event_id,
        event_type=event_type,
        reference=reference,
    )