from datetime import datetime

from sqlmodel import Field, SQLModel



class Booking(SQLModel, table=True):
	__tablename__ = "bookings"

	id: int | None = Field(default=None, primary_key=True)

	user_id: int = Field(foreign_key="users.id", index=True)
	showtime_id: int = Field(foreign_key="showtimes.id", index=True)

	reference: str = Field(unique=True, index=True)

	status: str = Field(default="pending", index=True)

	total_amount: float

	created_at: datetime = Field(default_factory=datetime.utcnow)