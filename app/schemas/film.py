from pydantic import BaseModel


class FilmCreate(BaseModel):
    title: str
    description: str
    duration_minutes: int
    rating: str


class FilmResponse(BaseModel):
    id: int
    title: str
    description: str
    duration_minutes: int
    rating: str