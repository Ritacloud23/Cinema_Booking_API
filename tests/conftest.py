import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.db.models import *


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
