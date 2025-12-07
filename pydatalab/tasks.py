import json
import os
import pathlib
import re
import time

from invoke import Collection, task

from pydatalab.logger import setup_log
from pydatalab.models.utils import UserRole

ns = Collection()
dev = Collection("dev")
admin = Collection("admin")
migration = Collection("migration")


def update_file(filename: str, sub_line: tuple[str, str], strip: str | None = None):
    """Utility function for tasks to read, update, and write files.

    Modified from optimade-python-tools.

    """
    with open(filename) as handle:
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
    """Registers a user account with the given identities."""
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
    """Generates refcodes for any items that are missing them."""
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
    response = requests.get(
        f"{base_url}/get-item-data/{id}", headers={"DATALAB-API-KEY": api_key}, timeout=30
    )
    if response.status_code != 200:
        log.error("ꙮ  %s: %s", id, response.content)


@task
def check_item_validity(_, base_url: str | None = None, starting_materials: bool = False):
    """This task looks up all sample and cell items and checks that they
    can be successfully accessed through the API.

    Requires the environment variable `DATALAB_API_KEY` to be set.
    Will also additionally pass JSON-formatted values from the `DATALAB_HEADERS` environment variable.

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

    headers = json.loads(os.environ.get("DATALAB_HEADERS", "{}"))
    headers.update({"DATALAB-API-KEY": api_key})

    log = setup_log("check_item_validity")

    user_response = requests.get(f"{base_url}/get-current-user/", headers=headers, timeout=30)
    if not user_response.status_code == 200:
        raise SystemExit(f"Could not get current user: {user_response.content!r}")

    all_samples_ids = [
        d["item_id"]
        for d in requests.get(f"{base_url}/samples/", headers=headers, timeout=30).json()["samples"]
    ]

    log.info("Found %s items", len(all_samples_ids))

    multiprocessing.Pool(max(min(len(all_samples_ids), 8), 1)).map(
        functools.partial(_check_id, api_key=api_key, base_url=base_url),
        all_samples_ids,
    )

    if starting_materials:
        all_starting_material_ids = [
            d["item_id"]
            for d in requests.get(
                f"{base_url}/starting-materials/", headers=headers, timeout=30
            ).json()["items"]
        ]
        multiprocessing.Pool(max(min(len(all_starting_material_ids), 8), 1)).map(
            functools.partial(_check_id, api_key=api_key, base_url=base_url),
            all_starting_material_ids,
        )


admin.add_task(check_item_validity)


@task
def check_remotes(_, base_url: str | None = None, invalidate_cache: bool = False):
    """This task looks up all configured remotes and checks that they
    can be synced.

    Requires the environment variable DATALAB_API_KEY to be set.
    Will also additionally pass JSON-formatted values from the DATALAB_HEADERS environment variable.

    Parameters:
        base_url: The API URL.
        invalidate_cache: Whether to force cache invalidation.

    """

    import os

    import requests

    api_key = os.environ.get("DATALAB_API_KEY")
    if not api_key:
        raise SystemExit("DATALAB_API_KEY env var not set")

    headers = json.loads(os.environ.get("DATALAB_HEADERS", "{}"))

    headers.update({"DATALAB-API-KEY": api_key})

    log = setup_log("check_remotes")

    user_response = requests.get(f"{base_url}/get-current-user/", headers=headers, timeout=30)
    if not user_response.status_code == 200:
        raise SystemExit(f"Could not get current user: {user_response.content!r}")

    directory_response = requests.get(
        f"{base_url}/list-remote-directories?invalidate_cache={'1' if invalidate_cache else '0'}",
        headers=headers,
        timeout=30,
    )

    if directory_response.status_code != 200:
        raise SystemExit(f"Could not get remote directories: {directory_response}")

    directory_structures = directory_response.json()["data"]

    for d in directory_structures:
        if d["status"] == "error":
            log.error("ꙮ %s: %s", d["name"], d["contents"][0]["details"])
        elif d["status"] == "cached":
            log.info("✩ %s: %s", d["name"], d["last_updated"])
        elif d["status"] == "updated":
            log.info("✓ %s: %s", d["name"], d["last_updated"])


admin.add_task(check_remotes)


@task
def import_cheminventory(_, filename: str | None = None):
    """For a given ChemInventory Excel export, ingest the .xlsx file at
    <filename> into the datalab items collection with type `starting_materials`.

    This task has been migrated to `datalab-api` package https://github.com/datalab-org/datalab-python-api
    as `datalab_api.helpers.import_cheminventory`.

    """

    raise NotImplementedError(
        "This task has been migrated to the `datalab-api` package as "
        "`datalab_api.helpers.import_cheminventory`: https://github.com/datalab-org/datalab-python-api"
    )


admin.add_task(import_cheminventory)


@task
def create_backup(
    _, strategy_name: str | None = None, output_path: pathlib.Path | str | None = None
):
    """Create a backup given the strategy name in the config or a local output path.

    If a strategy is not provided, this task will simply write a backup file
    to the chosen path (must end with .tar or .tar.gz).
    No retention policy will be applied, and remote backups are not possible
    via this route.

    If a strategy is provided, this task will create a backup file following all
    the configured settings, including retention and remote storage.

    This task could be added as a cronjob on the server, ideally using
    the frequency specified in the strategy to avoid confusion.

    Example usage in cron:

    ```shell
    crontab -e
    ```

    ```shell
    0 0 * * * /usr/local/bin/pipenv run invoke admin.create-backup --strategy-name=daily-snapshots
    ```

    """
    from pydatalab.backups import create_backup, take_snapshot
    from pydatalab.config import CONFIG

    if output_path and strategy_name:
        raise SystemExit("Cannot specify both an output path and a strategy name.")

    if output_path is not None:
        return take_snapshot(pathlib.Path(output_path))

    if strategy_name is not None:
        if not CONFIG.BACKUP_STRATEGIES:
            raise SystemExit("No backup strategies configured and output path not provided.")

        strategy = CONFIG.BACKUP_STRATEGIES.get(strategy_name)
        if strategy is None:
            raise SystemExit(f"Backup strategy {strategy_name!r} not found in config.")

    else:
        raise SystemExit("No backup strategy or output path provided.")

    return create_backup(strategy)


admin.add_task(create_backup)


@task
def restore_backup(_, snapshot_path: os.PathLike):
    from pathlib import Path

    from pydatalab.config import CONFIG

    user_input = input(
        f"!!! WARNING !!!\n\nThis is a destructive procedure and will:\n\t- overwrite any files currently saved at {CONFIG.FILE_DIRECTORY},\n\t- delete the database at {CONFIG.MONGO_URI}.\n\nInput [y] to continue, or anything else to abort: "
    )
    if user_input == "y":
        from pydatalab.backups import restore_snapshot

        print("Waiting 3 seconds for confirmation...")
        time.sleep(3)
        user_input = input("Are you sure? [y|n] ")

        if user_input == "y":
            print("Preparing to restore...")
            time.sleep(5)
            print("Restoring...")
            return restore_snapshot(Path(snapshot_path))

        print("Restore aborted.")


admin.add_task(restore_backup)

ns.add_collection(dev)
ns.add_collection(admin)
ns.add_collection(migration)
