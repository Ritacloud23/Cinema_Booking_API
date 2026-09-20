from pydantic import BaseModel


class SeatResponse(BaseModel):
    id: int
    showtime_id: int
    seat_number: str
    status: str