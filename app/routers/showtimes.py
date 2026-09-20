from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.security import require_role
from app.db.models.user import User
from app.db.session import get_session
from app.schemas.showtime import ShowtimeCreate, ShowtimeResponse
from app.services.showtime_service import create_showtime


router = APIRouter(
    prefix="/api/v1/showtimes",
    tags=["Showtimes"],
)


@router.post(
    "",
    response_model=ShowtimeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: ShowtimeCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role("manager")),
):
    try:
        return create_showtime(
            session=session,
            film_id=data.film_id,
            screen_id=data.screen_id,
            start_time=data.start_time,
            end_time=data.end_time,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )