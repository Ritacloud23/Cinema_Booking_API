from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class BookingSeat(SQLModel, table=True):
	__tablename__ = "booking_seats"

	__table_args__ = (
		UniqueConstraint("booking_id", "seat_inventory_id"),
	)

	id: int | None = Field(default=None, primary_key=True)

	booking_id: int = Field(foreign_key="bookings.id", index=True)
	seat_inventory_id: int = Field(
		foreign_key="seat_inventory.id",
		index=True,
	)

	created_at: datetime = Field(default_factory=datetime.utcnow)