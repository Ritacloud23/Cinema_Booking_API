from datetime import datetime

from sqlmodel import Field, SQLModel


class PriceRule(SQLModel, table=True):
    __tablename__ = "price_rules"

    id: int | None = Field(default=None, primary_key=True)

    film_id: int = Field(
        foreign_key="films.id",
        index=True,
    )

    name: str

    price: float

    starts_at: datetime

    ends_at: datetime

    priority: int = Field(default=0)

    active: bool = Field(default=True)

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )