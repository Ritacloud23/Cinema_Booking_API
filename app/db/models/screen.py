from datetime import datetime

from sqlmodel import Field, SQLModel



class Screen(SQLModel, table=True):
     __tablename__ = "screens"

     id: int | None = Field(default=None, primary_key=True)

     name: str = Field(unique=True, index=True)
     total_seats: int