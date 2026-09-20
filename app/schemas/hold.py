from pydantic import BaseModel
from datetime import datetime


class HoldCreate(BaseModel):
    seat_inventory_id: int


class HoldResponse(BaseModel):
    id: int
    seat_inventory_id: int
    user_id: int
    status: str
    expires_at: datetime