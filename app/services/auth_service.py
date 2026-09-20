from sqlmodel import Session, select

from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import User

def register_user(
   session: Session,
   email: str,
   password: str,
   full_name: str,
) -> User:
   existing_user = session.exec(
      select(User).where(User.email == email)
    ).first()
   if existing_user:
        raise ValueError("Email already registered")

   user = User(
       email=email,
       password_hash=hash_password(password),
       full_name=full_name,
       role="moviegoer",
     )
   
   session.add(user) 
   session.commit() 
   session.refresh(user) 
   

   return user


def login_user(
   session: Session,
   email: str,
   password: str,
) -> str:
  user = session.exec(
     select(User).where(User.email == email)
  ).first()  

  if user is None or not verify_password(password, user.password_hash):
     raise ValueError("Invalid email or password")

  return create_access_token(user.id, user.role)