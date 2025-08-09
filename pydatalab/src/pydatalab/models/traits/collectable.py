from pydantic import BaseModel, Field, model_validator

from pydatalab.models.collections import Collection


class IsCollectable(BaseModel):
    """Trait mixin for models that can be
    added to collections.
    """

    collections: list[Collection] = Field(
        default_factory=list,
        description="Inlined info for the collections associated with this item.",
    )

    @model_validator(mode="before")
    @classmethod
    def add_missing_collection_relationships(cls, values):
        if values.get("collections") is not None:
            collection_ids_set = set()

            for coll in values["collections"]:
                if isinstance(coll, dict):
                    immutable_id = coll.get("immutable_id")
                else:
                    immutable_id = getattr(coll, "immutable_id", None)
                if immutable_id:
                    collection_ids_set.add(immutable_id)

            existing_collection_relationship_ids = set()
            if values.get("relationships") is not None:
                for relationship in values["relationships"]:
                    if isinstance(relationship, dict):
                        rel_type = relationship.get("type")
                        if rel_type == "collections":
                            immutable_id = relationship.get("immutable_id")
                            if immutable_id:
                                existing_collection_relationship_ids.add(immutable_id)
                    else:
                        rel_type = getattr(relationship, "type", None)
                        if rel_type == "collections":
                            immutable_id = getattr(relationship, "immutable_id", None)
                            if immutable_id:
                                existing_collection_relationship_ids.add(immutable_id)
            else:
                values["relationships"] = []

            for collection_id in collection_ids_set:
                if collection_id not in existing_collection_relationship_ids:
                    relationship_dict = {
                        "relation": None,
                        "immutable_id": collection_id,
                        "type": "collections",
                        "description": "Is a member of",
                    }
                    values["relationships"].append(relationship_dict)

            values["relationships"] = [
                rel
                for rel in values["relationships"]
                if not (
                    (
                        isinstance(rel, dict)
                        and rel.get("type") == "collections"
                        and rel.get("immutable_id") not in collection_ids_set
                    )
                    or (
                        hasattr(rel, "type")
                        and rel.type == "collections"
                        and getattr(rel, "immutable_id", None) not in collection_ids_set
                    )
                )
            ]

        return values
