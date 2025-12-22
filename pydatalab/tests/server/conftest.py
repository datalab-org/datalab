from pathlib import Path

import pymongo
import pytest
from bson import ObjectId
from flask.testing import FlaskClient

from pydatalab.models import Cell, Collection, Equipment, Sample, StartingMaterial
from pydatalab.models.people import AccountStatus

TEST_DATABASE_NAME = "__datalab-testing__"


MONGO_URI = f"mongodb://localhost:27017/{TEST_DATABASE_NAME}"


@pytest.fixture(scope="module")
def real_mongo_client() -> pymongo.MongoClient | None:
    """Returns a connected MongoClient if available, otherwise `None`."""
    client = pymongo.MongoClient(
        MONGO_URI, connect=True, connectTimeoutMS=100, serverSelectionTimeoutMS=100
    )
    try:
        _ = client.list_database_names()
    except pymongo.errors.ServerSelectionTimeoutError:
        return None

    yield client
    client.close()


@pytest.fixture(scope="module")
def database(real_mongo_client):
    yield real_mongo_client.get_database(TEST_DATABASE_NAME)


@pytest.fixture(scope="session")
def app_config(tmp_path_factory, secret_key):
    example_remotes = [
        {
            "name": "example_data",
            "hostname": None,
            "path": Path(__file__).parent.parent.joinpath("../example_data/"),
        },
        {
            "name": "example/data",
            "hostname": None,
            "path": Path(__file__).parent.parent.joinpath("../example_data/"),
        },
    ]
    yield {
        "MONGO_URI": MONGO_URI,
        "REMOTE_FILESYSTEMS": example_remotes,
        "FILE_DIRECTORY": str(tmp_path_factory.mktemp("files")),
        "TESTING": False,
        "ROOT_PATH": "/",
        "SECRET_KEY": secret_key,
        "AUTO_ACTIVATE_ACCOUNTS": False,
        "EMAIL_AUTO_ACTIVATE_ACCOUNTS": False,
        "EMAIL_AUTH_SMTP_SETTINGS": {
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": 587,
            "MAIL_USERNAME": "test",
            "MAIL_USE_TLS": True,
            "MAIL_DEFAULT_SENDER": "test@example.org",
        },
        "EMAIL_DOMAIN_ALLOW_LIST": ["example.org", "ml-evs.science"],
        "MAIL_DEBUG": True,
        "MAIL_SUPPRESS_SEND": True,
        "MAIL_PASSWORD": "test",
        # Set to 10 MB to check that larger files fail; this should be larger than all of our example files.
        # Elsewhere, we can generate an artificial large file to check that it fails.
        "MAX_CONTENT_LENGTH": 10 * 1000**2,
    }


@pytest.fixture(scope="module")
def app(real_mongo_client, app_config):
    """Yields the test app."""
    from pydatalab.main import create_app
    from pydatalab.mongo import flask_mongo

    mongo_cli = real_mongo_client
    if mongo_cli is None:
        raise pymongo.errors.ServerSelectionTimeoutError(
            "Tests require a running local MongoDB instance."
        )

    databases = mongo_cli.list_database_names()

    if TEST_DATABASE_NAME in databases:
        mongo_cli.drop_database(TEST_DATABASE_NAME)

    app = create_app(app_config, env_file=False)

    yield app

    # Explicitly close the flask-pymongo connection
    if flask_mongo.cx:
        flask_mongo.cx.close()

    if mongo_cli:
        mongo_cli.drop_database(TEST_DATABASE_NAME)


def client_factory(app, api_key: str | None = None):
    """Generates a test client for the API with the given API key."""

    if api_key:

        class AuthorizedTestClient(FlaskClient):
            def open(self, *args, **kwargs):
                kwargs.setdefault("headers", {"DATALAB_API_KEY": api_key})
                return super().open(*args, **kwargs)

        app.test_client_class = AuthorizedTestClient
    else:
        app.test_client_class = FlaskClient

    with app.test_client() as cli:
        return cli


@pytest.fixture(scope="function")
def admin_client(app, admin_api_key):
    """Returns a test client for the API with admin access."""
    yield client_factory(app, admin_api_key)


@pytest.fixture(scope="function")
def client(app, user_api_key):
    """Returns a test client for the API with normal user access."""
    yield client_factory(app, user_api_key)


@pytest.fixture(scope="function")
def another_client(app, another_user_api_key):
    """Returns a test client for the API with a second normal user access."""
    yield client_factory(app, another_user_api_key)


@pytest.fixture(scope="function")
def unauthenticated_client(app):
    """Returns an unauthenticated test client for the API."""
    yield client_factory(app, None)


@pytest.fixture(scope="function")
def unverified_client(app, unverified_user_api_key):
    """Returns a test client for the API with an unverified user's credentials."""
    yield client_factory(app, unverified_user_api_key)


@pytest.fixture(scope="function")
def deactivated_client(app, deactivated_user_api_key):
    """Returns a test client for the API with a deactivated user's credentials."""
    yield client_factory(app, deactivated_user_api_key)


def generate_api_key():
    import random

    return "".join(random.choices("abcdef0123456789", k=24))  # noqa: S311


@pytest.fixture(scope="function")
def random_string():
    return generate_api_key()


@pytest.fixture(scope="session")
def admin_api_key() -> str:
    return generate_api_key()


@pytest.fixture(scope="session")
def user_api_key() -> str:
    return generate_api_key()


@pytest.fixture(scope="session")
def another_user_api_key() -> str:
    return generate_api_key()


@pytest.fixture(scope="session")
def unverified_user_api_key() -> str:
    return generate_api_key()


@pytest.fixture(scope="session")
def deactivated_user_api_key() -> str:
    return generate_api_key()


@pytest.fixture(scope="session")
def user_id():
    yield ObjectId(24 * "1")


@pytest.fixture(scope="session")
def group_id():
    yield ObjectId(24 * "2")


@pytest.fixture(scope="session")
def another_user_id():
    yield ObjectId(24 * "7")


@pytest.fixture(scope="session")
def admin_user_id():
    yield ObjectId(24 * "8")


@pytest.fixture(scope="session")
def unverified_user_id():
    yield ObjectId(24 * "2")


@pytest.fixture(scope="session")
def deactivated_user_id():
    yield ObjectId(24 * "3")


def insert_user(
    id,
    api_key,
    role,
    real_mongo_client,
    display_name: str = "Test Admin",
    status: AccountStatus = AccountStatus.ACTIVE,
    group_immutable_id: ObjectId | None = None,
):
    from hashlib import sha512

    demo_user = {
        "_id": id,
        "contact_email": "test@example.org",
        "display_name": display_name,
        "account_status": status,
    }
    if group_immutable_id is not None:
        demo_user["groups"] = [{"immutable_id": group_immutable_id}]

    real_mongo_client.get_database(TEST_DATABASE_NAME).users.insert_one(demo_user)
    hash = sha512(api_key.encode("utf-8")).hexdigest()
    real_mongo_client.get_database(TEST_DATABASE_NAME).api_keys.insert_one(
        {"_id": id, "hash": hash}
    )
    real_mongo_client.get_database(TEST_DATABASE_NAME).roles.insert_one({"_id": id, "role": role})


@pytest.fixture(scope="module", autouse=True)
def insert_demo_users(
    app,
    user_id,
    user_api_key,
    another_user_id,
    another_user_api_key,
    admin_user_id,
    admin_api_key,
    deactivated_user_id,
    deactivated_user_api_key,
    unverified_user_id,
    unverified_user_api_key,
    real_mongo_client,
    group_id,
):
    insert_user(
        user_id,
        user_api_key,
        "user",
        real_mongo_client,
        display_name="Test User",
        group_immutable_id=group_id,
    )
    insert_user(
        another_user_id,
        another_user_api_key,
        "user",
        real_mongo_client,
        display_name="Another User",
        group_immutable_id=group_id,
    )
    real_mongo_client.get_database(TEST_DATABASE_NAME).groups.insert_one(
        {"_id": group_id, "display_name": "Demo Group", "group_id": "demo"}
    )
    insert_user(admin_user_id, admin_api_key, "admin", real_mongo_client, display_name="Test Admin")
    insert_user(
        deactivated_user_id,
        deactivated_user_api_key,
        "user",
        real_mongo_client,
        display_name="Deactivated User",
        status=AccountStatus.DEACTIVATED,
    )
    insert_user(
        unverified_user_id,
        unverified_user_api_key,
        "user",
        real_mongo_client,
        display_name="Unverified User",
        status=AccountStatus.UNVERIFIED,
    )


@pytest.fixture(scope="module", name="default_sample")
def fixture_default_sample(admin_user_id, user_id, group_id):
    return Sample(
        **{
            "item_id": "12345",
            "name": "other_sample",
            "date": "1970-02-01",
            "type": "samples",
            "creator_ids": [admin_user_id, user_id],
            "group_ids": [group_id],
        }
    )


@pytest.fixture(scope="module", name="default_cell")
def fixture_default_cell(user_id):
    return Cell(
        **{
            "item_id": "test_cell",
            "name": "test cell",
            "date": "1970-02-01",
            "negative_electrode": [
                {
                    "item": {"item_id": "test", "chemform": "Li15Si4", "type": "samples"},
                    "quantity": 2.0,
                    "unit": "mg",
                },
                {
                    "item": {"item_id": "test", "chemform": "C", "type": "samples"},
                    "quantity": 2.0,
                    "unit": "mg",
                },
            ],
            "positive_electrode": [
                {
                    "item": {"item_id": "test_cathode", "chemform": "LiCoO2", "type": "samples"},
                    "quantity": 2000,
                    "unit": "kg",
                }
            ],
            "electrolyte": [{"item": {"name": "inlined reference"}, "quantity": 100, "unit": "ml"}],
            "cell_format": "swagelok",
            "type": "cells",
            "creator_ids": [user_id],
        }
    )


@pytest.fixture(scope="module", name="default_collection")
def fixture_default_collection():
    return Collection(
        **{
            "collection_id": "test_collection",
            "title": "My Test Collection",
            "date": "1970-02-02",
            "type": "collections",
        }
    )


@pytest.fixture(scope="module", name="default_starting_material")
def fixture_default_starting_material(admin_user_id):
    return StartingMaterial(
        **{
            "item_id": "test_sm",
            "chemform": "Na2CO3",
            "name": "Sodium carbonate",
            "date": "1992-12-11",
            "date_opened": "2022-12-11",
            "CAS": "497-19-8",
            "chemical_purity": "99%",
            "location": "SR1 room 22",
            "GHS_codes": "H303, H316, H319",
            "type": "starting_materials",
        }
    )


@pytest.fixture(scope="module", name="default_equipment")
def fixture_default_equipment():
    return Equipment(
        **{
            "item_id": "test_e1",
            "name": "a scientific instrument",
            "date": "1999-12-31",
            "location": "SR1 room 22",
            "manufacturer": "science inc.",
            "contact": "test@example.com",
            "serial_numbers": "1, 2a, 00-123-456z",
            "type": "equipment",
        }
    )


@pytest.fixture(scope="module", name="complicated_sample")
def fixture_complicated_sample(user_id):
    from pydatalab.models.utils import Constituent

    return Sample(
        **{
            "item_id": "sample_with_synthesis",
            "name": "complex_sample",
            "date": "1970-02-01",
            "chemform": "Na3P",
            "type": "samples",
            "creator_ids": [user_id],
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
def example_items(user_id, admin_user_id):
    """Create a collection of samples with mixed ownership between the user and admin."""
    return [
        d.dict(exclude_unset=False)
        for d in [
            Sample(
                **{
                    "item_id": "12345",
                    "name": "new material",
                    "description": "NaNiO2",
                    "date": "1970-02-01",
                    "refcode": "grey:TEST1",
                    "creator_ids": [user_id],
                }
            ),
            Sample(
                **{
                    "item_id": "123456",
                    "name": "new material",
                    "description": "NaNiO2",
                    "date": "1970-02-01",
                    "refcode": "grey:TEST10",
                    "creator_ids": [admin_user_id],
                }
            ),
            Sample(
                **{
                    "item_id": "56789",
                    "name": "alice",
                    "date": "1970-02-01",
                    "creator_ids": [user_id],
                }
            ),
            Sample(
                **{
                    "item_id": "sample_1",
                    "name": "bob",
                    "description": "12345",
                    "date": "1970-02-01",
                    "refcode": "grey:TEST2",
                    "creator_ids": [user_id],
                }
            ),
            Sample(
                **{
                    "item_id": "sample_admin",
                    "name": "bob",
                    "description": "magic",
                    "date": "1970-02-01",
                    "refcode": "grey:TEST9",
                    "creator_ids": [admin_user_id],
                }
            ),
            Sample(
                **{
                    "item_id": "sample_2",
                    "chemform": "vanadium(II) oxide",
                    "name": "other_sample",
                    "date": "1970-02-01",
                    "refcode": "grey:TEST3",
                    "creator_ids": [user_id],
                }
            ),
            StartingMaterial(
                **{
                    "item_id": "material",
                    "chemform": "NaNiO2",
                    "name": "new material",
                    "date": "1970-02-01",
                    "refcode": "grey:TEST4",
                    "creator_ids": [user_id],
                    "description": "magic",
                }
            ),
            StartingMaterial(
                **{
                    "item_id": "test",
                    "chemform": "NaNiO2",
                    "name": "NaNiO2",
                    "date": "1970-02-01",
                    "description": "magic",
                    "refcode": "grey:TEST5",
                    "creator_ids": [user_id],
                }
            ),
        ]
    ]


@pytest.fixture(scope="module", name="default_sample_dict")
def fixture_default_sample_dict(default_sample):
    return default_sample.dict(exclude_unset=True)


@pytest.fixture(scope="module", name="default_cell_dict")
def fixture_default_cell_dict(default_cell):
    return default_cell.dict(exclude_unset=True)


@pytest.fixture(scope="module", name="default_starting_material_dict")
def fixture_default_starting_material_dict(default_starting_material):
    return default_starting_material.dict(exclude_unset=True)


@pytest.fixture(scope="module", name="default_equipment_dict")
def fixture_default_equipment_dict(default_equipment):
    return default_equipment.dict(exclude_unset=True)


def _insert_and_cleanup_item_from_model(model):
    from pydatalab.models.utils import generate_unique_refcode
    from pydatalab.mongo import flask_mongo

    refcode = generate_unique_refcode()
    model.refcode = refcode
    flask_mongo.db.items.insert_one(model.dict(exclude_unset=False))
    yield model
    flask_mongo.db.items.delete_one({"refcode": model.refcode})


@pytest.fixture(scope="module", name="insert_default_sample")
def fixture_insert_default_sample(default_sample):
    yield from _insert_and_cleanup_item_from_model(default_sample)


@pytest.fixture(scope="module", name="insert_default_cell")
def fixture_insert_default_cell(default_cell):
    yield from _insert_and_cleanup_item_from_model(default_cell)


@pytest.fixture(scope="module", name="insert_default_starting_material")
def fixture_insert_default_starting_material(default_starting_material):
    yield from _insert_and_cleanup_item_from_model(default_starting_material)


@pytest.fixture(scope="module", name="insert_default_equipment")
def fixture_insert_default_equipment(default_equipment):
    yield from _insert_and_cleanup_item_from_model(default_equipment)


@pytest.fixture(scope="module", name="insert_example_items")
def fixture_insert_example_items(example_items, real_mongo_client):
    real_mongo_client.get_database(TEST_DATABASE_NAME).items.delete_many({})
    real_mongo_client.get_database().items.insert_many(example_items)


@pytest.fixture(scope="module", name="inserted_default_items")
def fixture_inserted_default_items(
    insert_default_sample,
    insert_default_cell,
    insert_default_starting_material,
    insert_default_equipment,
):
    return [insert_default_sample, insert_default_cell, insert_default_starting_material]
