from datetime import datetime

from sqlmodel import Field, SQLModel



class User(SQLModel, table=True):
   __tablename__ = "users"

   id: int | None = Field(default=None, primary_key=True)

   email: str = Field(unique=True, index=True)
   password_hash: str
   full_name: str

   role: str = Field(default="moviegoer")

   created_at: datetime = Field(default_factory=datetime.utcnow)