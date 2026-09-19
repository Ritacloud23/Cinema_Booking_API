from datetime import datetime

from sqlmodel import Field, SQLModel


class Showtime(SQLModel, table=True):
	__tablename__ = "showtimes"

	id: int | None = Field(default=None, primary_key=True)

	film_id: int = Field(foreign_key="films.id", index=True)
	screen_id: int = Field(foreign_key="screens.id", index=True)

	start_time: datetime
	end_time: datetime

	created_at: datetime = Field(default_factory=datetime.utcnow)