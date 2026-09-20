from pydantic import BaseModel


class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    reference: str
    amount: float
    currency: str
    status: str


class PaymentWebhook(BaseModel):
    event_id: str
    type: str
    reference: str
    amount: float
    currency: str
    paid_at: str