import json
import pathlib
import re
import sys
from typing import Tuple

from invoke import Collection, task

from pydatalab.logger import setup_log
from pydatalab.models.utils import UserRole

ns = Collection()
dev = Collection("dev")
admin = Collection("admin")
migration = Collection("migration")


def update_file(filename: str, sub_line: Tuple[str, str], strip: str | None = None):
    """Utility function for tasks to read, update, and write files.

    Modified from optimade-python-tools.

    """
    with open(filename, "r") as handle:
        lines = [re.sub(sub_line[0], sub_line[1], line.rstrip(strip)) for line in handle]

    with open(filename, "w") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")


@task
def generate_schemas(_):
    """This task generates JSONSchemas for all item models used in the project."""
    from pydatalab.models import ITEM_MODELS

    schemas_path = pathlib.Path(__file__).parent / "schemas"

    for model in ITEM_MODELS.values():
        schema = model.schema(by_alias=False)
        with open(schemas_path / f"{model.__name__.lower()}.json", "w") as f:
            json.dump(schema, f, indent=2)


dev.add_task(generate_schemas)


@task(help={"ver": "New Datalab version to set"})
def set_version(_, ver=""):
    """Sets the datalab package version

    Modified from optimade-python-tools.

    """
    match = re.fullmatch(r"v?([0-9]+\.[0-9]+\.[0-9]+)", ver)
    if not match or (match and len(match.groups()) != 1):
        print("Error: Please specify version as 'Major.Minor.Patch' or 'vMajor.Minor.Patch'")
        sys.exit(1)
    ver = match.group(1)

    update_file(
        pathlib.Path(__file__).parent.resolve().joinpath("pydatalab/__init__.py"),
        (r'__version__ = ".*"', f'__version__ = "{ver}"'),
    )

    print("Bumped version to {}".format(ver))


dev.add_task(set_version)


@task
def create_mongo_indices(_):
    """This task creates the default MongoDB indices defined in the main code."""
    from pydatalab.mongo import create_default_indices

    create_default_indices()


admin.add_task(create_mongo_indices)


@task
def change_user_role(_, display_name: str, role: UserRole):
    """This task takes a user's name and gives them the desired role."""
    from bson import ObjectId

    from pydatalab.mongo import _get_active_mongo_client

    try:
        role = getattr(UserRole, role.upper())
    except AttributeError:
        raise SystemExit(f"Invalid role: {role!r}. Must be one of {UserRole.__members__}") from None

    matches = list(
        _get_active_mongo_client().datalabvue.users.find(
            {"$text": {"$search": display_name}}, projection={"_id": 1, "display_name": 1}
        )
    )
    if len(matches) > 1:
        raise SystemExit(
            f"Too many matches for display name {display_name!r}: {[_['display_name'] for _ in matches]}"
        )

    if len(matches) == 0:
        raise SystemExit(f"No matches for display name {display_name!r}")
    user_str = f"{matches[0]['display_name']} ({matches[0]['_id']})"
    print(f"Found user: {user_str}")
    user_id = ObjectId(matches[0]["_id"])

    role_results = _get_active_mongo_client().datalabvue.roles.find_one({"_id": user_id})
    if role_results and role_results["role"] == role:
        raise SystemExit(
            f"User {user_str} already has role: {role_results['role']!r}: will not update"
        )

    _get_active_mongo_client().datalabvue.roles.update_one(
        {"_id": user_id}, {"$set": {"role": role}}, upsert=True
    )

    print(f"Updated {display_name} to {role}.")


admin.add_task(change_user_role)


@task
def manually_register_user(
    _,
    display_name: str,
    contact_email: str,
    orcid: str | None = None,
    github_user_id: int | None = None,
):
    from pydatalab.models.people import Identity, Person

    identities = []
    if github_user_id:
        identities.append(
            Identity(identity_type="github", identifier=github_user_id, verified=False)
        )

    if orcid:
        identities.append(Identity(identity_type="orcid", identifier=orcid, verified=False))

    if contact_email:
        identities.append(
            Identity(
                identity_type="email", identifier=contact_email, name=contact_email, verified=False
            )
        )

    new_user = Person(
        display_name=display_name,
        contact_email=contact_email,
        identities=identities,
    )

    from pydatalab.mongo import insert_pydantic_model_fork_safe

    insert_pydantic_model_fork_safe(new_user, "users")


admin.add_task(manually_register_user)


@task
def repair_files(_, resync: bool = True):
    """Loop through samples and find any with attached files
    that are no longer stored on disk. If available, try to
    sync them with remote versions of the files.

    """

    from pydatalab.file_utils import _check_and_sync_file
    from pydatalab.models.files import File
    from pydatalab.mongo import _get_active_mongo_client

    cli = _get_active_mongo_client()

    for ind, item in enumerate(
        cli.datalabvue.items.find({"$or": [{"type": "samples"}, {"type": "cells"}]})
    ):
        print(ind, end="\r")
        for file_id in item.get("file_ObjectIds", []):
            file_data = cli.datalabvue.files.find_one({"_id": file_id})
            path = file_data.get("location", None)
            if not path:
                continue
            path = pathlib.Path(path)
            if not path.exists():
                if resync and file_data.get("source_server_name") is not None:
                    print(f"Attempting to resync {path}, {file_id}")
                    _check_and_sync_file(File(**file_data), file_id)
                else:
                    print(
                        f"Item {item['item_id']} is missing file: {file_data['name']!r}, ({file_id})"
                    )


admin.add_task(repair_files)


@task
def add_missing_refcodes(_):
    from pydatalab.models.utils import generate_unique_refcode
    from pydatalab.mongo import get_database

    db = get_database()

    for item in db.items.find({"refcode": None}, projection={"refcode": 1, "_id": 1}):
        if item.get("refcode") is None:
            refcode = generate_unique_refcode()
            print(f"Assigning {item['_id']} with {refcode}")
            db.items.update_one({"_id": item["_id"]}, {"$set": {"refcode": refcode}})


migration.add_task(add_missing_refcodes)


def _check_id(id=None, base_url=None, api_key=None):
    """Checks the given item ID served at the base URL and logs the result."""
    import requests

    log = setup_log("check_item_validity")
    response = requests.get(f"{base_url}/get-item-data/{id}", headers={"DATALAB-API-KEY": api_key})
    if response.status_code != 200:
        log.error(f"ꙮ {id!r}: {response.content!r}")


@task
def check_item_validity(_, base_url: str | None = None, starting_materials: bool = False):
    """This task looks up all sample and cell items and checks that they
    can be successfully accessed through the API.

    Requires the environment variable DATALAB_API_KEY to be set.

    Parameters:
        base_url: The API URL.
        starting_materials: Whether to check starting materials as well.

    """

    import functools
    import multiprocessing
    import os

    import requests

    api_key = os.environ.get("DATALAB_API_KEY")
    if not api_key:
        raise SystemExit("DATALAB_API_KEY env var not set")

    log = setup_log("check_item_validity")

    user_response = requests.get(
        f"{base_url}/get-current-user/", headers={"DATALAB-API-KEY": api_key}
    )
    if not user_response.status_code == 200:
        raise SystemExit(f"Could not get current user: {user_response.json()['message']}")

    all_samples_ids = [
        d["item_id"]
        for d in requests.get(f"{base_url}/samples/", headers={"DATALAB-API-KEY": api_key}).json()[
            "samples"
        ]
    ]

    log.info(f"Found {len(all_samples_ids)} items")

    multiprocessing.Pool(max(min(len(all_samples_ids), 8), 1)).map(
        functools.partial(_check_id, api_key=api_key, base_url=base_url),
        all_samples_ids,
    )

    if starting_materials:
        all_starting_material_ids = [
            d["item_id"]
            for d in requests.get(
                f"{base_url}/starting-materials/", headers={"DATALAB-API-KEY": api_key}
            ).json()["items"]
        ]
        multiprocessing.Pool(max(min(len(all_starting_material_ids), 8), 1)).map(
            functools.partial(_check_id, api_key=api_key, base_url=base_url),
            all_starting_material_ids,
        )


admin.add_task(check_item_validity)


@task
def import_cheminventory(_, filename: str):
    import random

    import pandas as pd

    from pydatalab.models import StartingMaterial
    from pydatalab.models.utils import generate_unique_refcode
    from pydatalab.mongo import get_database

    def generate_random_startingmaterial_id():
        """
        This function generates XX + a random 15-length string for use as an id for starting materials
        that don't have a barcode.
        """

        randlist = ["XX"] + random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=15)

        return "".join(randlist)

    data_collection = get_database().items

    df = pd.read_excel(filename)
    df["type"] = "starting_materials"  # all starting materials will have this as the type
    df["item_id"] = df["Barcode"]  # assign item_id to be the Barcode by default

    # some starting materials don't have a barcode. Create a random id for those.
    replacement_dict = {
        i: generate_random_startingmaterial_id() for i, _ in df[df.item_id.isna()].iterrows()
    }
    df.item_id.fillna(value=replacement_dict, inplace=True)

    # clean the molecular weight column:
    df["Molecular Weight"].replace(" ", float("nan"), inplace=True)

    # convert df to list of dictionaries for ingestion into mongo
    df.to_dict(orient="records")

    # filter out missing values
    ds = [
        {k: v for k, v in d.items() if (v != "None" and pd.notnull(v))}
        for d in df.to_dict(orient="records")
    ]

    starting_materials = []
    for d in ds:
        d["refcode"] = generate_unique_refcode()
        starting_materials.append(StartingMaterial(**d))

    # update or insert all starting materials
    for starting_material in starting_materials:
        print(f"adding starting material {starting_material.item_id} ({starting_material.name})")
        data_collection.update_one(
            {"item_id": starting_material.item_id}, {"$set": starting_material.dict()}, upsert=True
        )

    print("Done!")


admin.add_task(import_cheminventory)


ns.add_collection(dev)
ns.add_collection(admin)
ns.add_collection(migration)
