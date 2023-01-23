from pathlib import Path
from typing import Union
from unittest.mock import patch

import mongomock
import pymongo
import pytest

import pydatalab.mongo
from pydatalab.main import create_app
from pydatalab.models import Sample, StartingMaterial


class PyMongoMock(mongomock.MongoClient):
    def init_app(self, _):
        return super().__init__()


# Must remain as `db` so that calls to flask_mongo.db remain correct
TEST_DATABASE_NAME = "db"
MONGO_URI = f"mongodb://localhost:27017/{TEST_DATABASE_NAME}"


@pytest.fixture(scope="session")
def real_mongo_client() -> Union[pymongo.MongoClient, None]:
    """Returns a connected MongoClient if available, otherwise `None`."""
    client = pymongo.MongoClient(
        MONGO_URI, connect=True, connectTimeoutMS=100, serverSelectionTimeoutMS=100
    )
    try:
        _ = client.list_database_names()
    except pymongo.errors.ServerSelectionTimeoutError:
        return None

    return client


@pytest.fixture(scope="session")
def client(real_mongo_client):
    """Returns a test client for the API. If it exists,
    connects to a local MongoDB, otherwise uses the
    mongomock testing backend.

    """

    example_remote = {
        "name": "example_data",
        "hostname": None,
        "path": Path(__file__).parent.joinpath("../example_data/"),
    }

    try:
        mongo_cli = real_mongo_client
        if mongo_cli is None:
            raise pymongo.errors.ServerSelectionTimeoutError

        databases = mongo_cli.list_database_names()

        if TEST_DATABASE_NAME in databases:
            raise RuntimeError(
                f"Not running tests over the top of existing database named {TEST_DATABASE_NAME!r} at {MONGO_URI}; "
                "try dropping it before running the tests if this is desired."
            )

        app = create_app(
            {
                "MONGO_URI": MONGO_URI,
                "REMOTE_FILESYSTEMS": [example_remote],
                "TESTING": True,
            }
        )

        with app.test_client() as cli:
            yield cli

        mongo_cli.drop_database(TEST_DATABASE_NAME)

    except pymongo.errors.ServerSelectionTimeoutError:
        with patch.object(
            pydatalab.mongo,
            "flask_mongo",
            PyMongoMock(connectTimeoutMS=100, serverSelectionTimeoutMS=100),
        ):
            app = create_app(
                {
                    "MONGO_URI": MONGO_URI,
                    "REMOTE_FILESYSTEMS": [example_remote],
                }
            )

            with app.test_client() as cli:
                yield cli


@pytest.fixture(scope="module", name="default_sample")
def fixture_default_sample():
    return Sample(**{"item_id": "12345", "name": "other_sample", "date": "1970-02-01"})


@pytest.fixture(scope="module", name="complicated_sample")
def fixture_complicated_sample():
    from pydatalab.models.samples import Constituent

    return Sample(
        **{
            "item_id": "sample_with_synthesis",
            "name": "complex_sample",
            "date": "1970-02-01",
            "chemform": "Na3P",
            "synthesis_constituents": [
                Constituent(
                    **{
                        "item": {
                            "item_id": "starting_material_1",
                            "name": "first Na",
                            "chemform": "Na",
                            "type": "starting_materials",
                        },
                        "quantity": 1,
                    }
                ),
                Constituent(
                    **{
                        "item": {
                            "item_id": "starting_material_2",
                            "name": "second Na",
                            "chemform": "Na",
                            "type": "starting_materials",
                        },
                        "quantity": 2,
                        "unit": "kg",
                    }
                ),
                Constituent(
                    **{
                        "item": {
                            "item_id": "starting_material_3",
                            "name": "liquid Na",
                            "chemform": "Na",
                            "type": "starting_materials",
                        },
                        "quantity": 3,
                        "unit": "ml",
                    }
                ),
            ],
            "synthesis_description": "Take one gram of sodium and add 2 kg of...sodium, then 3 ml of liquid sodium(??) <i>et voila</i>, you have some real good sodium!",
        }
    )


@pytest.fixture(scope="module")
def example_items():
    return [
        d.dict(exclude_unset=False)
        for d in [
            Sample(
                **{
                    "item_id": "12345",
                    "name": "new material",
                    "description": "NaNiO2",
                    "date": "1970-02-01",
                }
            ),
            Sample(**{"item_id": "56789", "name": "alice", "date": "1970-02-01"}),
            Sample(
                **{
                    "item_id": "sample_1",
                    "name": "bob",
                    "description": "12345",
                    "date": "1970-02-01",
                }
            ),
            Sample(**{"item_id": "sample_2", "name": "other_sample", "date": "1970-02-01"}),
            StartingMaterial(
                **{
                    "item_id": "material",
                    "chemform": "NaNiO2",
                    "name": "new material",
                    "date_acquired": "1970-02-01",
                }
            ),
            StartingMaterial(
                **{
                    "item_id": "test",
                    "chemform": "NaNiO2",
                    "name": "NaNiO2",
                    "date_acquired": "1970-02-01",
                }
            ),
        ]
    ]


@pytest.fixture(scope="module", name="default_sample_dict")
def fixture_default_sample_dict(default_sample):
    return default_sample.dict(exclude_unset=True)
