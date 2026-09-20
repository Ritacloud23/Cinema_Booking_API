from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.seat_inventory import SeatResponse
from app.services.seatmap_service import (
    generate_seats,
    get_seat_map,
)


router = APIRouter(
    prefix="/api/v1/showtimes",
    tags=["Seat Inventory"],
)


@router.post(
    "/{showtime_id}/seats",
    response_model=list[SeatResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_seats(
    showtime_id: int,
    session: Session = Depends(get_session),
):
    try:
        return generate_seats(
            session=session,
            showtime_id=showtime_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get(
    "/{showtime_id}/seats",
    response_model=list[SeatResponse],
)
def get_seats(
    showtime_id: int,
    session: Session = Depends(get_session),
):
    try:
        return get_seat_map(
            session=session,
            showtime_id=showtime_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )