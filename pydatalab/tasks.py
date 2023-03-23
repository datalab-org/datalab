import json
import pathlib

from invoke import Collection, task

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

    for ind, item in enumerate(cli.datalabvue.items.find({"type": "samples"})):
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


ns.add_collection(dev)
ns.add_collection(admin)
ns.add_collection(migration)
