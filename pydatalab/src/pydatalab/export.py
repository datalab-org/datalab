"""This module implements methods for exporting datalab data
to other formats, such as .eln files.

"""

import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId

from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER
from pydatalab.models import ITEM_MODELS
from pydatalab.mongo import flask_mongo

__all__ = ("generate_ro_crate_metadata", "create_eln_file")


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
                "@id": f"./{item['item_id']}/",
            }
        )

    graph: list[dict] = [
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "about": {"@id": "./"},
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
            "dateCreated": datetime.now(tz=timezone.utc).isoformat(),
            "sdPublisher": {
                "@id": CONFIG.IDENTIFIER_PREFIX or "https://github.com/datalab-org/datalab"
            },
        },
        {
            "@id": "./",
            "@type": "Dataset",
            "name": collection_data.get("title", collection_data.get("collection_id")),
            "description": collection_data.get("description", ""),
            "hasPart": experiments,
        },
    ]

    metadata = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": graph,
    }

    for item in child_items:
        item_metadata = {
            "@id": f"./{item['item_id']}/",
            "@type": "Dataset",
            "name": item.get("name", item["item_id"]),
            "identifier": item["item_id"],
            "dateCreated": item.get("date", datetime.now(tz=timezone.utc)).isoformat()
            if isinstance(item.get("date"), datetime)
            else item.get("date"),
        }

        if item.get("file_ObjectIds"):
            files = []
            for file_id in item["file_ObjectIds"]:
                file_data = flask_mongo.db.files.find_one({"_id": ObjectId(file_id)})
                if file_data:
                    files.append({"@id": f"./{item['item_id']}/{file_data['name']}"})
            if files:
                item_metadata["hasPart"] = files

        graph.append(item_metadata)

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

    if collection_id:
        # We are outside the request context here, so cannot easily apply permissions baesd on the user.
        # TODO: Extra safeguards here -- refactor default permissions finder to be able to use
        # an externally set user ID

        collection_data = flask_mongo.db.collections.find_one({"collection_id": collection_id})
        if not collection_data:
            raise ValueError(f"Collection {collection_id} not found")

        collection_immutable_id = collection_data["_id"]
        child_items = list(
            flask_mongo.db.items.find(
                {
                    "relationships": {
                        "$elemMatch": {
                            "type": "collections",
                            "immutable_id": collection_immutable_id,
                        }
                    }
                }
            )
        )
        root_folder_name = collection_id

    elif item_id:
        # TODO: same comment about permissions as above
        item_data = flask_mongo.db.items.find_one({"item_id": item_id})
        if not item_data:
            raise ValueError(f"Item {item_id} not found")

        if related_item_ids:
            child_items = list(
                flask_mongo.db.items.find({"item_id": {"$in": [item_id] + related_item_ids}})
            )
        else:
            child_items = [item_data]

        collection_data = {
            "collection_id": item_id,
            "title": item_data.get("name", item_id),
            "description": f"Export of item {item_id}"
            + (" and related items" if related_item_ids else ""),
        }
        root_folder_name = item_id

    else:
        raise ValueError("Either collection_id or item_id must be provided")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        root_folder = temp_path / root_folder_name
        root_folder.mkdir()

        ro_crate_metadata = generate_ro_crate_metadata(collection_data, child_items)
        with open(root_folder / "ro-crate-metadata.json", "w", encoding="utf-8") as f:
            json.dump(ro_crate_metadata, f, indent=2, ensure_ascii=False)

        for item in child_items:
            item_folder = root_folder / item["item_id"]
            item_folder.mkdir()

            item_metadata = ITEM_MODELS[item.get("type")](**item).json(indent=2)

            with open(item_folder / "metadata.json", "w", encoding="utf-8") as f:
                f.write(item_metadata)

            if item.get("file_ObjectIds"):
                for file_id in item.get("file_ObjectIds", []):
                    file_id_obj = ObjectId(file_id) if isinstance(file_id, str) else file_id
                    file_data = flask_mongo.db.files.find_one({"_id": file_id_obj})
                    if file_data:
                        source_path = Path(file_data["location"])
                        if source_path.exists():
                            dest_file = item_folder / file_data["name"]
                            shutil.copy2(source_path, dest_file)
                        else:
                            LOGGER.warning(
                                "ELN export: File not found on disk: %s", file_data["location"]
                            )
                    else:
                        LOGGER.warning(
                            "ELN export: File metadata not found in database for file_id: %s",
                            file_id,
                        )

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in root_folder.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_path)
                    zipf.write(file_path, arcname)
