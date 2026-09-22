from datetime import datetime

from sqlmodel import Field, SQLModel


class Film(SQLModel, table=True):
    __tablename__ = "films"

    id: int | None = Field(default=None, primary_key=True)

    title: str = Field(index=True)
    description: str
    duration_minutes: int
    rating: str

    base_price: float

    created_at: datetime = Field(default_factory=datetime.utcnow)