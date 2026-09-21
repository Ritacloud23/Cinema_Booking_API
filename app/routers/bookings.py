from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.security import get_current_user
from app.db.models.user import User
from app.db.session import get_session
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
)
from app.services.booking_service import create_booking


router = APIRouter(
    prefix="/api/v1/bookings",
    tags=["Bookings"],
)


@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: BookingCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_booking(
            session=session,
            user_id=current_user.id,
            hold_id=data.hold_id,
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    except ValueError as exc:
        message = str(exc)

        if message in {
            "Hold not found",
            "Seat not found",
        }:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        )