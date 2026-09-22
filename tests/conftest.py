import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db.models import *
from app.db.session import get_session
from app.main import app


TEST_DATABASE_URL = (
    "postgresql+psycopg://screenhive:screenhive_password"
    "@localhost:5432/screenhive_test"
)

test_engine = create_engine(
    TEST_DATABASE_URL,
    echo=False,
)


@pytest.fixture
def session():
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        yield session

    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def client():
    SQLModel.metadata.create_all(test_engine)

    def override_get_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(test_engine)