import json
import os
import pathlib
import re
import shutil
import subprocess
import time
import typing

import tomlkit
from invoke import Collection, task

if typing.TYPE_CHECKING:
    from pydatalab.models.utils import UserRole

ns = Collection()
dev = Collection("dev")
admin = Collection("admin")
migration = Collection("migration")


# Path to the canonical plugins.toml location, at the root of the repository
# (one level above pydatalab/). Resolving via __file__ lets the task be invoked
# from any working directory.
PLUGINS_TOML_PATH = pathlib.Path(__file__).resolve().parent.parent / "plugins.toml"


def load_plugin_schema():
    """Return the top-level pydantic model describing the plugins.toml schema.

    The model classes are defined inside this helper to keep the top level of
    `tasks.py` uncluttered: only `dev.install` and `dev.generate-schemas`
    need them. A JSON Schema generated from the returned model is emitted to
    `pydatalab/schemas/plugin_config.json` by `invoke dev.generate-schemas`.
    """
    from pydantic import BaseModel, root_validator

    class UvSource(BaseModel):
        """A single entry under `[tool.uv.sources]` in plugins.toml."""

        git: str | None = None
        rev: str | None = None
        branch: str | None = None
        tag: str | None = None
        path: str | None = None
        editable: bool | None = None

        class Config:
            extra = "forbid"

        @root_validator
        def _exactly_one_source(cls, values):
            has_git = values.get("git") is not None
            has_path = values.get("path") is not None
            if has_git and has_path:
                raise ValueError("a uv source must specify either `git` or `path`, not both")
            if not has_git and not has_path:
                raise ValueError("a uv source must specify one of `git` or `path`")
            return values

    class UvSection(BaseModel):
        sources: dict[str, UvSource] = {}

        class Config:
            extra = "forbid"

    class ToolSection(BaseModel):
        uv: UvSection = UvSection()

        class Config:
            extra = "forbid"

    class PluginConfigModel(BaseModel):
        """The schema for the top-level plugins.toml file."""

        dependencies: list[str] = []
        tool: ToolSection = ToolSection()

        class Config:
            extra = "forbid"

        @root_validator
        def _sources_must_match_dependencies(cls, values):
            deps = {d.split("[")[0].strip() for d in values.get("dependencies", [])}
            sources = values.get("tool", ToolSection()).uv.sources
            orphans = sorted(set(sources) - deps)
            if orphans:
                raise ValueError(
                    f"[tool.uv.sources] entries have no matching dependency: {orphans}"
                )
            return values

    return PluginConfigModel


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

    with open(schemas_path / "plugin_config.json", "w") as f:
        json.dump(load_plugin_schema().schema(), f, indent=2)


dev.add_task(generate_schemas)


@task(
    help={
        "host": "Host to bind",
        "port": "Port to bind",
        "reload": "Enable the Werkzeug reloader and debugger (disable with --no-reload)",
        "testing": "Enable CONFIG.TESTING if PYDATALAB_TESTING is not already set",
    }
)
def serve(_, host: str = "127.0.0.1", port: int = 5001, reload: bool = True, testing: bool = False):
    """Boot the Flask development server."""
    from dotenv import load_dotenv

    # Load .env into os.environ *first*, before the guards below and before
    # importing pydatalab.main (which instantiates the CONFIG singleton).
    # Otherwise the `not in os.environ` checks pass spuriously and the dev
    # fallbacks shadow any real values from .env, since pydantic ranks
    # os.environ above the .env file.
    env_path = pathlib.Path(__file__).parent / ".env"

    if not env_path.is_file():
        print(f"No .env file found at {env_path}, proceeding with environment variables alone.")

    load_dotenv(env_path)

    if testing and "PYDATALAB_TESTING" not in os.environ:
        os.environ["PYDATALAB_TESTING"] = "1"

    if "PYDATALAB_SECRET_KEY" not in os.environ:
        os.environ["PYDATALAB_SECRET_KEY"] = "dev-insecure-secret-key-do-not-use-in-production"  # noqa: S105
        os.environ["PYDATALAB_ALLOW_INSECURE_SECRET_KEY"] = "1"  # noqa: S105

    from pydatalab.main import create_app

    create_app(env_file=env_path).run(host=host, port=port, debug=reload, use_reloader=reload)


dev.add_task(serve)


# Example data for `dev.seed`, grouped by the block that renders it. Each group
# is expanded by `_build_seed_items` into one seeded item per file (a single
# block per item), so a fresh dev instance exercises every block type that has
# example data. Groups flagged `single_item` instead produce one item carrying
# the whole file list -- used for multi-file blocks (uv-vis: first file is the
# background) and file-less blocks (comment). All paths are relative to
# `pydatalab/example_data/` and only list files the parser actually accepts;
# companion files (Biologic .mps/.sta, gzipped JEOL, READMEs) are omitted.
_SEED_BLOCK_GROUPS: list[dict] = [
    {
        "block_type": "xrd",
        "item_type": "samples",
        "files": [
            "XRD/CG20396_jdb12-1.xrdml",
            "XRD/HL1-2_5-90_60min.xrdml",
            "XRD/JO_KL_16_ZF_3_60deg_0.02step_12degpermin_001.rasx",
            "XRD/TiO2.raw",
            "XRD/TiOF.brml",
            "XRD/cod_9004112.cif",
            "XRD/example_bmb.xye",
            "XRD/example_evadiffract.xy",
            "XRD/example_mac.xye",
            "XRD/example_mythen.dat",
            "XRD/example_mythen.xye",
            "XRD/example_ocx.xy",
            "XRD/Scan_C1.xrdml",
            "XRD/Scan_C2.xrdml",
            "XRD/Scan_C3.xrdml",
            "XRD/Scan_C4.xrdml",
            "XRD/Scan_C5.xrdml",
            "XRD/Scan_C6.xrdml",
            "XRD/Scan_C7.xrdml",
            "XRD/Scan_C8.xrdml",
            "XRD/Scan_C9.xrdml",
            "XRD/Scan_C10.xrdml",
        ],
    },
    {
        "block_type": "raman",
        "item_type": "samples",
        "files": [
            "raman/labspec_raman_example.txt",
            "raman/raman_example.txt",
            "raman/raman_example.wdf",
        ],
    },
    {
        "block_type": "cycle",
        "item_type": "cells",
        "files": [
            "echem/arbin_example.bdf.csv",
            "echem/jdb11-1_c3_gcpl_5cycles_2V-3p8V_C-24_data_C09.mpr",
            "echem/jdb11-1_e1_s3_squidTest_data_C15.mpr",
        ],
    },
    {
        "block_type": "nmr",
        "item_type": "samples",
        "files": [
            "NMR/1.zip",  # Bruker 1D
            "NMR/1h.dx",  # JCAMP-DX
            "NMR/13c.jdx",  # JCAMP-DX
            "NMR/71.zip",  # Bruker 1D
            # 72.zip (2D dataset: metadata only, no plot) and multi_nuclei.zip
            # (selects an experiment with no Bruker binary) are omitted -- the
            # block only renders 1D data.
        ],
    },
    {
        "block_type": "ftir",
        "item_type": "samples",
        "files": [
            "FTIR/2024-10-10_FeSO4_ref.asp",
            "FTIR/[FTIRText]020.txt",
        ],
    },
    {
        "block_type": "ms",
        "item_type": "samples",
        "files": [
            "TGA-MS/20221128 134958 TGA MS Megan.asc",
            # mp2028_281122_LNO+C.txt is omitted: the ms parser decodes as UTF-8
            # and that file contains a latin-1 degree sign, raising a decode error.
        ],
    },
    {
        "block_type": "tabular",
        "item_type": "samples",
        "files": [
            "csv/simple.csv",
            "csv/simple.xlsx",
        ],
    },
    {
        "block_type": "media",
        "item_type": "samples",
        "files": [
            "media/grey_group_logo.jpeg",
            "media/grey_group_logo.tif",
        ],
    },
    {
        # A single uv-vis block needs >=2 files; the first is the background scan.
        "block_type": "uv-vis",
        "item_type": "samples",
        "single_item": True,
        "name": "UV-Vis example (background + scans)",
        "files": [
            "UV-Vis/1908047U1_0000.Raw8.TXT",
            "UV-Vis/1908047U1_0001.Raw8.txt",
            "UV-Vis/1908047U1_0060.Raw8.txt",
        ],
    },
    {
        # File-less block: the text lives in the `freeform_comment` field.
        "block_type": "comment",
        "item_type": "samples",
        "single_item": True,
        "name": "Comment example",
        "files": [],
        "block_data": {
            "freeform_comment": "Seeded comment block — rich-text notes attached to a sample.",
        },
    },
]

# Items seeded without any block, for item-type variety.
_SEED_EXTRA_ITEMS: list[dict] = [
    {
        "payload": {
            "item_id": "seed_starting_material",
            "type": "starting_materials",
            "name": "Example starting material",
            "chemform": "Na2CO3",
            "description": "Seeded starting material.",
        },
        "block_type": None,
        "files": [],
        "block_data": {},
    },
]


# `item_id` is validated to be at most this many characters (see the item models),
# so generated ids are truncated to fit.
_MAX_ITEM_ID_LENGTH = 40


def _slug(value: str) -> str:
    """Lowercase `value` and collapse any run of non-alphanumerics into a single underscore."""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _make_item_id(base: str, used: set[str]) -> str:
    """Slugify `base`, truncate to the item-id length limit, and disambiguate collisions.

    Deterministic given a stable input order, so re-running `dev.seed` yields the same
    ids (keeping it idempotent).
    """
    candidate = _slug(base)[:_MAX_ITEM_ID_LENGTH].rstrip("_")
    if candidate not in used:
        used.add(candidate)
        return candidate
    i = 2
    while True:
        suffix = f"_{i}"
        candidate = (_slug(base)[: _MAX_ITEM_ID_LENGTH - len(suffix)].rstrip("_")) + suffix
        if candidate not in used:
            used.add(candidate)
            return candidate
        i += 1


def _build_seed_items() -> list[dict]:
    """Expand `_SEED_BLOCK_GROUPS` into a flat list of item specs for `dev.seed`.

    Each spec is a dict with keys `payload` (the `/new-sample/` body), `block_type`
    (or `None` for no block), `files` (example_data-relative paths) and `block_data`
    (extra fields merged into the block before rendering).
    """
    items: list[dict] = []
    used_ids: set[str] = set()
    for group in _SEED_BLOCK_GROUPS:
        block_type = group["block_type"]
        item_type = group["item_type"]
        block_data = group.get("block_data", {})

        if group.get("single_item"):
            name = group.get("name", f"{block_type} example")
            items.append(
                {
                    "payload": {
                        "item_id": _make_item_id(f"seed_{block_type}", used_ids),
                        "type": item_type,
                        "name": name,
                        "description": group.get("description", f"Seeded {block_type} example."),
                    },
                    "block_type": block_type,
                    "files": list(group["files"]),
                    "block_data": dict(block_data),
                }
            )
            continue

        for rel_path in group["files"]:
            filename = pathlib.PurePosixPath(rel_path).name
            items.append(
                {
                    "payload": {
                        "item_id": _make_item_id(f"seed_{block_type}_{filename}", used_ids),
                        "type": item_type,
                        "name": f"{block_type} example: {filename}",
                        "description": f"Seeded {block_type} example from {filename}.",
                    },
                    "block_type": block_type,
                    "files": [rel_path],
                    "block_data": dict(block_data),
                }
            )

    items.extend(_SEED_EXTRA_ITEMS)
    return items


_SEED_ITEMS = _build_seed_items()


@task
def seed(_):
    """Populate the configured database with a comprehensive set of example items.

    Seeds one item per example file under `pydatalab/example_data/`, attaching and
    rendering the matching technique block, so a fresh development instance covers
    every block type that has example data (xrd, raman, cycle, nmr, ftir, ms,
    uv-vis, tabular, media), plus a comment block and a starting material. Connect
    to whichever database `PYDATALAB_MONGO_URI` points at.

    Idempotent: items that already exist (matched by `item_id`) are skipped, so
    it is safe to re-run. Forces `CONFIG.TESTING` for this process so items and
    files can be created without authentication.
    """
    import io

    os.environ["PYDATALAB_TESTING"] = "1"
    if "PYDATALAB_SECRET_KEY" not in os.environ:
        os.environ["PYDATALAB_SECRET_KEY"] = "dev-insecure-secret-key-do-not-use-in-production"  # noqa: S105
        os.environ["PYDATALAB_ALLOW_INSECURE_SECRET_KEY"] = "1"  # noqa: S105

    from pydatalab.main import create_app

    example_data = pathlib.Path(__file__).parent / "example_data"

    app = create_app()
    created = skipped = 0
    with app.test_client() as client:
        for spec in _SEED_ITEMS:
            payload = spec["payload"]
            item_id = payload["item_id"]
            resp = client.post("/new-sample/", json={"new_sample_data": payload})

            if resp.status_code == 409:
                print(f"  - {item_id}: already exists, skipping")
                skipped += 1
                continue
            if resp.status_code not in (200, 201):
                print(
                    f"  ! {item_id}: create failed ({resp.status_code}): {resp.get_data(as_text=True)}"
                )
                continue

            print(f"  + {item_id}: created")
            created += 1

            block_type = spec["block_type"]
            if block_type is None:
                continue

            # Upload each example file and attach it to the item, preserving order
            # (the first file is the background scan for multi-file blocks).
            file_ids: list[str] = []
            for rel_path in spec["files"]:
                file_path = example_data / rel_path
                if not file_path.is_file():
                    print(f"    ! example file not found, skipping: {file_path}")
                    continue
                with open(file_path, "rb") as handle:
                    upload = client.post(
                        "/upload-file/",
                        data={
                            "item_id": item_id,
                            "replace_file": "null",
                            "file": (io.BytesIO(handle.read()), file_path.name),
                        },
                        content_type="multipart/form-data",
                    )
                if upload.status_code != 201:
                    print(f"    ! file upload failed for {file_path.name} ({upload.status_code})")
                    continue
                file_ids.append(upload.get_json()["file_id"])

            # Create the data block, wire in the uploaded file(s) and any extra
            # block fields, then render it.
            add = client.post(
                "/add-data-block/",
                json={"block_type": block_type, "item_id": item_id, "index": 0},
            )
            if add.status_code != 200:
                print(f"    ! adding {block_type} block failed ({add.status_code})")
                continue
            block_data = add.get_json()["new_block_obj"]
            if len(file_ids) == 1:
                block_data["file_id"] = file_ids[0]
            elif len(file_ids) > 1:
                # Multi-file blocks (e.g. uv-vis) read the ordered file list.
                block_data["file_ids"] = file_ids
                block_data["selected_file_order"] = file_ids
            block_data.update(spec["block_data"])

            update = client.post("/update-block/", json={"block_data": block_data})
            detail = f"{len(file_ids)} file(s)" if file_ids else "no file"
            if update.status_code == 200:
                print(f"    ✓ rendered {block_type} block ({detail})")
            else:
                print(f"    ! rendering {block_type} block failed ({update.status_code})")

    print(f"\nSeed complete: {created} created, {skipped} skipped.")


dev.add_task(seed)


@task
def install(_, dev=True):
    """This task looks for a plugins.toml and attempts to
    do an isolated build in `./build` with its own lock
    and pyproject.toml.

    """

    plugin_cfg = PLUGINS_TOML_PATH

    deps: list[str] = []
    sources: dict[str, dict[str, str]] = {}

    if not plugin_cfg.is_file():
        print(f"No plugins.toml found at {plugin_cfg}; installing with base pyproject.toml")

    else:
        with open(plugin_cfg) as f:
            raw_plugin_data = tomlkit.load(f)

        try:
            plugin_data = load_plugin_schema().parse_obj(raw_plugin_data.unwrap())
        except Exception as exc:
            raise SystemExit(f"Invalid plugins.toml at {plugin_cfg}:\n{exc}") from None

        deps = list(plugin_data.dependencies)
        sources = {
            name: source.dict(exclude_none=True)
            for name, source in plugin_data.tool.uv.sources.items()
        }

        print(f"Found plugins: {deps}")

        # Resolve any relative paths in [tool.uv.sources] relative to the
        # location of plugins.toml itself (i.e. the repo root).
        for name, source in sources.items():
            if source.get("path") is not None:
                sources[name]["path"] = str((plugin_cfg.parent / source["path"]).resolve())

    with open(pathlib.Path(__file__).parent / "pyproject.toml") as f:
        pyproject_data = dict(tomlkit.load(f))

    pyproject_data["tool"]["setuptools_scm"]["root"] = "../.."

    if deps:
        pyproject_data["project"] = pyproject_data.get("project", {})
        pyproject_data["project"]["optional-dependencies"] = pyproject_data["project"].get(
            "optional-dependencies", {}
        )

        if "plugins" in pyproject_data["project"]["optional-dependencies"]:
            raise SystemExit(
                "The pyproject.toml already has a plugins optional-dependencies block, cannot continue."
            )

        pyproject_data["project"]["optional-dependencies"]["plugins"] = deps

        original_sources = pyproject_data.get("tool", {}).get("uv", {}).get("sources", {})
        original_sources.update(sources)

    build_dir = pathlib.Path(__file__).parent / "build"
    build_dir.mkdir(exist_ok=True)

    print(f"Installing datalab into {build_dir} with custom pyproject.toml and uv.lock...")

    new_pyproject_path = build_dir / "pyproject.toml"
    if new_pyproject_path.is_file():
        new_pyproject_path.unlink()

    # dump to ./build/pyproject.toml
    with open(new_pyproject_path, "w") as f:
        tomlkit.dump(pyproject_data, f)

    # copy existing lock then rerun uv lock to create ./build/uv.lock
    shutil.copy(pathlib.Path(__file__).parent / "uv.lock", build_dir / "uv.lock")
    subprocess.run(["uv", "lock"], cwd=build_dir, check=True)  # noqa: S607

    print(
        "Combining environment with plugins and installing into base datalab virtual environment `./.venv"
    )

    sync_cmd = ["uv", "sync", "--locked", "--all-extras", "--active", "--project", "./build"]
    if not dev:
        sync_cmd.append("--no-dev")

    subprocess.run(sync_cmd, check=True)  # noqa: S607, S603

    # Finally, install datalab-server in editable mode so that it can be run from the source directory, in the same way
    # we do in the Docker build
    install_cmd = ["uv", "pip", "install", "-e", "."]
    subprocess.run(install_cmd, check=True)  # noqa: S607, S603

    print("Done! To revert to locked core dependencies, run `uv sync --all-extras --dev`.")


dev.add_task(install)


@task
def create_mongo_indices(_):
    """This task creates the default MongoDB indices defined in the main code."""
    from pydatalab.mongo import create_default_indices

    create_default_indices()


admin.add_task(create_mongo_indices)


@task
def change_user_role(_, display_name: str, role: "UserRole"):
    """This task takes a user's name and gives them the desired role."""
    from bson import ObjectId

    from pydatalab.models.utils import UserRole
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
    from pydatalab.logger import setup_log

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

    from pydatalab.logger import setup_log

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

    from pydatalab.logger import setup_log

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
def cleanup_files(_):
    """This task looks for any files in the file storage directory that are
    not referenced by any items in the database and logs by filename, printing
    a summary to stderr. Can be piped to xargs/rm to actually delete the files.

    """
    from pydatalab.mongo import get_database

    files = get_database().files
    items = get_database().items

    total_size = 0
    orphans = 0
    marked = 0
    for file_doc in files.find(projection={"_id": 1, "location": 1, "size": 1}):
        file_id = file_doc["_id"]
        location = file_doc["location"]
        size_bytes = file_doc.get("size", 0) or 0

        if location and items.find_one({"file_ObjectIds": file_id}, projection={"_id": 1}) is None:
            loc = pathlib.Path(location)
            marked += 1
            if loc.is_file() or loc.parent.is_dir():
                print(loc.parent)
                total_size += size_bytes
            else:
                orphans += 1

    print(
        f"{marked} unreferenced files found, totaling {total_size / 1e9:.2f} GB, with {orphans} orphaned references to non-existent files.",
        file=os.sys.stderr,
    )


admin.add_task(cleanup_files)


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
