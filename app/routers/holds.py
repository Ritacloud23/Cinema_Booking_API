from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.security import get_current_user
from app.db.models.user import User
from app.db.session import get_session
from app.schemas.hold import HoldCreate, HoldResponse
from app.services.hold_service import create_hold


router = APIRouter(
    prefix="/api/v1/holds",
    tags=["Holds"],
)


@router.post(
    "",
    response_model=HoldResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: HoldCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_hold(
            session=session,
            user_id=current_user.id,
            seat_inventory_id=data.seat_inventory_id,
        )

    except ValueError as exc:
        message = str(exc)

        if message == "Seat not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        )