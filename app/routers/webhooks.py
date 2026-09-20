import hashlib
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel import Session

from app.core.config import settings
from app.db.session import get_session
from app.schemas.payment import PaymentWebhook
from app.services.payment_service import process_payment_webhook


router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Webhooks"],
)


@router.post("/payment")
def payment_webhook(
    data: PaymentWebhook,
    x_signature: str = Header(...),
    session: Session = Depends(get_session),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Webhook signature verification will be added next",
    )