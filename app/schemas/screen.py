from pydantic import BaseModel


class ScreenCreate(BaseModel):
    name: str
    total_seats: int


class ScreenResponse(BaseModel):
    id: int
    name: str
    total_seats: int