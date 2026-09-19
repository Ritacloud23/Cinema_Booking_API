from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel



class SeatInventory(SQLModel, table=True):
	__tablename__ = "seat_inventory"

	__table_args__ = (
		UniqueConstraint("showtime_id", "seat_number"),
	)

	id: int | None = Field(default=None, primary_key=True)

	showtime_id: int = Field(foreign_key="showtimes.id", index=True)
	seat_number: str = Field(index=True)

	status: str = Field(default="available", index=True)

	created_at: datetime = Field(default_factory=datetime.utcnow)