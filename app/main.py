from fastapi import Depends, FastAPI

from app.core.security import get_current_user
from app.db.models.user import User

from app.routers.auth import router as auth_router
from app.routers.holds import router as hold_router
from app.routers.films import router as film_router
from app.routers.screens import router as screen_router
from app.routers.showtimes import router as showtime_router
from app.routers.seatmap import router as seatmap_router
from app.routers.bookings import router as booking_router
from app.routers.payments import router as payment_router
from app.routers.webhooks import router as webhook_router
from app.middleware.request import request_middleware
from app.routers.stream import router as stream_router
from contextlib import asynccontextmanager
from app.jobs.expire_holds import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


app = FastAPI(
    title="ScreenHive API",
    version="1.0.0",
    lifespan=lifespan,

 )



app.middleware("http")(request_middleware)
app.include_router(auth_router)
app.include_router(hold_router)
app.include_router(film_router)
app.include_router(screen_router)
app.include_router(showtime_router)
app.include_router(seatmap_router)
app.include_router(booking_router)
app.include_router(payment_router)
app.include_router(webhook_router)
app.include_router(stream_router)



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