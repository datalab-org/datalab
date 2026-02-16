"""This module implements methods for exporting datalab data
to other formats, such as .eln files.

"""

import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from pydatalab import __version__
from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER
from pydatalab.models import ITEM_MODELS
from pydatalab.mongo import flask_mongo
from pydatalab.routes.v0_1.items import (
    collections_lookup,
    creators_lookup,
    files_lookup,
    groups_lookup,
)

__all__ = ("generate_ro_crate_metadata", "create_eln_file")


def write_eln_file(root_folder_name, items, info, output_path) -> None:
    """Write an ELN file to disk containing the given items and collection metadata.
    Will first write to an intermediate temporary directory.

    Parameters:
        root_folder_name: The name of the root folder in the ELN file.
        items: List of items to include in the ELN file, with all metadata and file info included.
        info: Metadata for the collection (or item) being exported.
        output_path: Path where the .eln file should be saved.

    """

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        root_folder = temp_path / root_folder_name
        root_folder.mkdir()

        ro_crate_metadata = generate_ro_crate_metadata(info, items)
        with open(root_folder / "ro-crate-metadata.json", "w", encoding="utf-8") as f:
            json.dump(ro_crate_metadata, f, ensure_ascii=False)

        for item in items:
            item_folder = root_folder / item["refcode"]
            item_folder.mkdir()

            item_metadata = ITEM_MODELS[item.get("type")](**item).json(indent=2)

            with open(item_folder / "metadata.json", "w", encoding="utf-8") as f:
                f.write(item_metadata)

            for file in item.get("files", []):
                source_path = Path(file["location"])
                if source_path.exists():
                    dest_file = item_folder / file["name"]
                    shutil.copy2(source_path, dest_file)
                else:
                    LOGGER.warning("ELN export: File not found on disk: %s", file["location"])

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in root_folder.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_path)
                    zipf.write(file_path, arcname)


def generate_ro_crate_metadata(collection_data: dict, child_items: list[dict]) -> dict:
    """Generate RO-Crate metadata for the .eln file.

    Parameters:
        collection_data: The collection metadata
        child_items: List of items in the collection

    Returns:
        RO-Crate metadata as a dictionary
    """

    experiments: list[dict] = []
    for item in child_items:
        experiments.append(
            {
                "@id": f"./{item['refcode']}/",
            }
        )

    now = datetime.now(tz=timezone.utc).isoformat()

    graph: list[dict] = [
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "about": {"@id": "./"},
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
            "dateCreated": now,
        },
        {
            "@id": "./",
            "@type": "Dataset",
            "name": collection_data.get("title", collection_data.get("collection_id")),
            "description": collection_data.get("description", ""),
            "hasPart": experiments,
            "version": "1",
            "license": {
                "@id": "https://choosealicense.com/no-permission/",
            },
            "datePublished": now,
        },
    ]

    if CONFIG.APP_URL:
        graph[0]["sdPublisher"] = {"@id": CONFIG.APP_URL}
        graph.append(
            {
                "@id": CONFIG.APP_URL,
                "@type": "Organization",
                "name": "datalab instance",
                "description": f"datalab instance running at {CONFIG.APP_URL}",
                "url": CONFIG.APP_URL,
            }
        )

    metadata = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": graph,
    }

    people = {}

    for item in child_items:
        identifier = f"{CONFIG.IDENTIFIER_PREFIX}:{item['refcode']}"

        item_metadata = {
            "@id": f"./{item['refcode']}/",
            "@type": "Dataset",
            "name": item.get("name", item["item_id"]),
            "identifier": identifier,
            "url": f"https://purl.datalab-org.io/{identifier}",
        }

        item_metadata["authors"] = [
            {"@id": f"./people/{c['immutable_id']}"} for c in item.get("creators", [])
        ]

        for creator in item.get("creators", []):
            # Need to refer to ORCID
            people[creator["immutable_id"]] = {
                "@id": f"./people/{creator['immutable_id']}",
                "@type": "Person",
                "name": creator.get("display_name"),
            }
        if not item_metadata["authors"]:
            del item_metadata["authors"]

        date_created = item.get("date")
        if date_created:
            item_metadata["dateCreated"] = date_created.isoformat()

        files = []
        files_metadata: list[dict] = []
        for file in item.get("files", []):
            file_id = f"./{item['refcode']}/{file['name']}"
            files.append({"@id": file_id})

            file_metadata = {
                "@id": file_id,
                "@type": "File",
                "contentSize": file["size"],
                "name": file["name"],
            }

            if file.get("last_modified"):
                file_metadata["dateCreated"] = file["last_modified"].isoformat()

            files_metadata.append(file_metadata)

        # Add file for datalab metadata
        item_metadata_file = {
            "@id": f"./{item['refcode']}/metadata.json",
            "@type": "File",
            "name": "metadata.json",
            "encodingFormat": "application/json",
            "description": f"Metadata for item {item['refcode']}",
        }

        files.append({"@id": item_metadata_file["@id"]})
        files_metadata.append(item_metadata_file)

        if files:
            item_metadata["hasPart"] = files

        graph.append(item_metadata)
        if files_metadata:
            graph.extend(files_metadata)
        if people:
            graph.extend(people.values())

        create_action = {
            "@id": "#ro-crate-created",
            "@type": "CreateAction",
            "object": {"@id": "./"},
            "endTime": datetime.now(tz=timezone.utc).isoformat(),
            "instrument": {"@id": "https://datalab-org.io"},
            "actionStatus": {"@id": "http://schema.org/CompletedActionStatus"},
        }

        software = {
            "@id": "https://datalab-org.io",
            "@type": "SoftwareApplication",
            "name": "datalab",
            "version": __version__,
        }

        graph.append(create_action)
        graph.append(software)

    return metadata


def create_eln_file(
    output_path: str,
    collection_id: str | None = None,
    item_id: str | None = None,
    related_item_ids: list[str] | None = None,
) -> None:
    """Create a .eln file for a collection, item, or set of items.

    Parameters:
        collection_id: ID of the collection to export
        output_path: Path where the .eln file should be saved
        item_id: ID of the item to export
        related_item_ids: List of related item IDs to include in the export.

    """
    if not collection_id and not item_id:
        raise ValueError("Either collection_id or item_id must be provided")

    match: dict = {}

    if collection_id:
        # We are outside the request context here, so cannot easily apply permissions baesd on the user.
        # TODO: Extra safeguards here -- refactor default permissions finder to be able to use
        # an externally set user ID

        collection_data = flask_mongo.db.collections.find_one({"collection_id": collection_id})
        if not collection_data:
            raise ValueError(f"Collection {collection_id} not found")

        collection_immutable_id = collection_data["_id"]

        match = {
            "relationships": {
                "$elemMatch": {
                    "type": "collections",
                    "immutable_id": collection_immutable_id,
                }
            }
        }

        root_folder_name = collection_id

    elif item_id:
        match = {"item_id": item_id}
        # Find main item info first; error out if missing
        cursor = flask_mongo.db.items.aggregate(
            [
                {
                    "$match": {
                        **match,
                    }
                },
                {"$lookup": creators_lookup()},
                {"$lookup": groups_lookup()},
                {"$lookup": collections_lookup()},
                {"$lookup": files_lookup()},
            ],
        )

        try:
            item_data = list(cursor)[0]
            ItemModel = ITEM_MODELS[item_data["type"]]
            item_data = ItemModel(**item_data).dict()

        except IndexError:
            item_data = None

        if not item_data:
            raise ValueError(f"Item {item_id} not found")

        root_folder_name = item_data["refcode"]

        if related_item_ids:
            match = {"item_id": {"$in": [item_id] + related_item_ids}}  # type: ignore

        collection_data = {
            "collection_id": item_id,
            "title": item_data.get("name", item_id),
            "description": f"Export of item {item_id}"
            + (" and related items" if related_item_ids else ""),
        }

    else:
        raise ValueError("Either collection_id or item_id must be provided")

    all_items = flask_mongo.db.items.aggregate(
        [
            {
                "$match": {
                    **match,
                }
            },
            {"$lookup": creators_lookup()},
            {"$lookup": groups_lookup()},
            {"$lookup": collections_lookup()},
            {"$lookup": files_lookup()},
        ],
    )

    _all_items = []

    for ind, item in enumerate(all_items):
        ItemModel = ITEM_MODELS[item["type"]]
        _all_items.append(ItemModel(**item).dict())

    all_items = _all_items

    write_eln_file(root_folder_name, all_items, collection_data, output_path)
