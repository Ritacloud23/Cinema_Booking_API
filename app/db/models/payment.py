from datetime import datetime

from sqlmodel import Field, SQLModel


class Payment(SQLModel, table=True):
	__tablename__ = "payments"

	id: int | None = Field(default=None, primary_key=True)

	booking_id: int = Field(foreign_key="bookings.id", index=True)

	reference: str = Field(unique=True, index=True)

	amount: float
	currency: str = Field(default="NGN")

	status: str = Field(default="pending", index=True)

	created_at: datetime = Field(default_factory=datetime.utcnow)