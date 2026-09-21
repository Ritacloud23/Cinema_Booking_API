from datetime import datetime

from pydantic import BaseModel


class ShowtimeCreate(BaseModel):
    film_id: int
    screen_id: int
    start_time: datetime
    end_time: datetime
    ticket_price: float


class ShowtimeResponse(BaseModel):
    id: int
    film_id: int
    screen_id: int
    start_time: datetime
    end_time: datetime
    ticket_price: float