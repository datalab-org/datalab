from unittest.mock import patch

import mongomock
import pytest

import pydatalab.mongo
from pydatalab.main import create_app
from pydatalab.models import Sample


class PyMongoMock(mongomock.MongoClient):
    def init_app(self, _):
        return super().__init__()


# Must remain as `db` so that calls to flask_mongo.db remain correct
TEST_DATABASE_NAME = "db"
MONGO_URI = f"mongodb://localhost:27017/{TEST_DATABASE_NAME}"


@pytest.fixture(scope="session")
def client():
    with patch.object(
        pydatalab.mongo,
        "flask_mongo",
        PyMongoMock(connectTimeoutMS=100, serverSelectionTimeoutMS=100),
    ):
        app = create_app({"TESTING": True, "MONGO_URI": MONGO_URI})

        with app.test_client() as cli:
            yield cli


@pytest.fixture(scope="module", name="default_sample")
def fixture_default_sample():
    return Sample(**{"item_id": "12345", "name": "other_sample", "date": "1970-02-01"})


@pytest.fixture(scope="module", name="default_sample_dict")
def fixture_default_sample_dict(default_sample):
    return default_sample.dict(exclude_unset=True)
