from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.security import require_role
from app.db.models.user import User
from app.db.session import get_session
from app.schemas.screen import (
    ScreenCreate,
    ScreenResponse,
)
from app.services.screen_service import (
    create_screen,
    get_screens,
)


router = APIRouter(
    prefix="/api/v1/screens",
    tags=["Screens"],
)


@router.post(
    "",
    response_model=ScreenResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: ScreenCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role("manager")),
):
    try:
        return create_screen(
            session=session,
            name=data.name,
            total_seats=data.total_seats,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[ScreenResponse],
)
def list_screens(
    session: Session = Depends(get_session),
):
    return get_screens(session)