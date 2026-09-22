from pydantic import BaseModel


class FilmCreate(BaseModel):
    title: str
    description: str
    duration_minutes: int
    rating: str
    base_price: float


class FilmResponse(BaseModel):
    id: int
    title: str
    description: str
    duration_minutes: int
    rating: str
    base_price: float