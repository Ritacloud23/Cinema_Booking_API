from fastapi import FastAPI
from fastapi import Depends

from app.core.security import get_current_user
from app.db.models.user import User
from app.routers.auth import router as auth_router

app = FastAPI(title="ScreenHive API")



@app.get("/")
def home():
    return {"message": "ScreenHive API is running"}


@app.get("/api/v1/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
      "id": current_user.id,
      "email": current_user.email,
      "full_name": current_user.full_name,
      "role": current_user.role,
     }
