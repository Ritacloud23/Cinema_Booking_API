from fastapi import Depends, FastAPI

from app.core.security import get_current_user
from app.db.models.user import User
from app.routers.auth import router as auth_router
from app.routers.holds import router as hold_router
from app.routers.films import router as film_router
from app.routers.showtimes import router as showtime_router
from app.routers.seatmap import router as seatmap_router
from app.routers.bookings import router as booking_router

app = FastAPI(title="ScreenHive API")

app.include_router(auth_router)
app.include_router(hold_router)
app.include_router(film_router)
app.include_router(showtime_router)
app.include_router(seatmap_router)
app.include_router(booking_router)


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