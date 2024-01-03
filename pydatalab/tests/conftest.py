from pathlib import Path

import pytest


@pytest.fixture(scope="module", name="default_filepath")
def fixture_default_filepath():
    return Path(__file__).parent.joinpath(
        "../example_data/echem/jdb11-1_c3_gcpl_5cycles_2V-3p8V_C-24_data_C09.mpr"
    )


@pytest.fixture(scope="module", name="insert_default_sample")
def fixture_insert_default_sample(client, default_sample):  # pylint: disable=unused-argument
    from pydatalab.mongo import flask_mongo

    flask_mongo.db.items.insert_one(default_sample.dict(exclude_unset=False))
    yield
    flask_mongo.db.items.delete_one({"item_id": default_sample.item_id})
