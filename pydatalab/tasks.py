import json
import pathlib

from invoke import Collection, task

from pydatalab.logger import setup_log
from pydatalab.models.utils import UserRole

ns = Collection()
dev = Collection("dev")
admin = Collection("admin")
migration = Collection("migration")


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
    orcid: str = None,
    github_user_id: int = None,
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
def check_item_validity(_, base_url: str = None, starting_materials: bool = False):
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


ns.add_collection(dev)
ns.add_collection(admin)
ns.add_collection(migration)
