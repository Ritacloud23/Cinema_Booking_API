from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.security import require_role
from app.db.models.user import User
from app.db.session import get_session
from app.schemas.film import FilmCreate, FilmResponse
from app.services.film_service import create_film, get_films


router = APIRouter(
    prefix="/api/v1/films",
    tags=["Films"],
)


@router.post(
    "",
    response_model=FilmResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: FilmCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role("manager")),
):
    return create_film(
        session,
        data.title,
        data.description,
        data.duration_minutes,
        data.rating,
        data.base_price,
    )


@router.get(
    "",
    response_model=list[FilmResponse],
)
def list_films(
    session: Session = Depends(get_session),
):
    return get_films(session)