from pydantic import BaseModel


class BookingCreate(BaseModel):
    hold_id: int


class BookingResponse(BaseModel):
    id: int
    user_id: int
    showtime_id: int
    reference: str
    status: str
    total_amount: float