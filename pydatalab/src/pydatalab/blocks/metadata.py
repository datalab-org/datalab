"""Resolving a block's metadata, and keeping track of where each value came from.

A block's metadata is rarely all from one place. A sample mass might be written
into a data file by the instrument, a molar mass derived from the sample's
chemical formula, and either of them corrected by hand. Which of those a value
came from is worth knowing -- it is the difference between a number the
instrument measured and one somebody typed -- and it decides what happens to that
value later.

Each field is *bound* to a source, and it is the binding that persists rather
than the value:

- Bound to a source, the value is re-read every time the block renders, so it
  follows the file if the file is replaced, or the sample if the sample is
  edited.
- Bound to the user, the value is what the user gave and nothing recomputes it.
- Bound to nothing, the sources are tried in order until one has a value. This is
  the block's own guess, so it is made again each time and is free to change its
  mind when a new file arrives.

The rule that decides between those: the system's choices stay open, and the
user's choices are kept. Clearing a field by hand is a choice -- it says there is
no good value for this -- so it is kept too, and is not the same state as a field
nobody has touched.
"""

from typing import Any

from pydantic import BaseModel

__all__ = ("USER", "AUTO", "MetadataResolution", "resolve_metadata")

USER = "user"
"""The binding for a value the user gave, which is stored rather than re-read."""

AUTO = "auto"
"""Not a binding: asking for this clears one, putting the field back to guessing."""


class MetadataResolution(BaseModel):
    """The outcome of resolving one block's metadata."""

    metadata: BaseModel
    """The values in force, as the block's own metadata model."""

    fields: dict[str, dict[str, Any]]
    """Per field, the value, the source it came from, and what the other sources
    have to offer -- which is what lets the interface say where a number came from
    and offer the alternatives."""

    model_config = {"arbitrary_types_allowed": True}


def _coerce(metadata: BaseModel, field: str, value: Any) -> Any:
    """Put a value through the model, returning what it became, or None.

    A file is free to contain nonsense in a field nobody needs, so a value the
    model rejects is dropped rather than allowed to fail the whole block.
    """
    try:
        setattr(metadata, field, value)
    except Exception:  # noqa: S110 -- a bad value is one missing value, not an error
        return None
    return getattr(metadata, field)


def resolve_metadata(
    model: type[BaseModel],
    sources: dict[str, dict],
    bindings: dict[str, dict] | None = None,
) -> MetadataResolution:
    """Work out each field's value, and record where it came from.

    Args:
        model: The block's metadata model. Every field must be optional, since a
            block fills in whatever its sources happen to have.
        sources: What each source offers, best first, e.g.
            `{"file": {...}, "sample": {...}}`. Every source is read, whether or
            not it wins, so that the interface can offer them all.
        bindings: The bindings the user has set, as `{field: {"source": ...}}`,
            carrying a `"value"` as well when the source is the user.

    """
    bindings = bindings or {}
    metadata = model()
    # A separate instance to try candidate values on, so that reading what a source
    # offers cannot leave anything behind on the model being built.
    probe = model()
    fields: dict[str, dict[str, Any]] = {}

    for field in model.model_fields:
        # Everything each source has for this field, in the order they were given.
        available = {
            name: _coerce(probe, field, values.get(field))
            for name, values in sources.items()
            if field in values
        }

        binding = bindings.get(field)
        source: str | None
        value: Any
        if binding and binding.get("source") == USER:
            source, value = USER, binding.get("value")
        elif binding and binding.get("source") in available:
            source, value = binding["source"], available[binding["source"]]
        elif binding:
            # Bound to a source the block no longer has: a file replaced by one
            # that does not carry this field, say. Left empty rather than quietly
            # falling back, which would undo a choice somebody made.
            source, value = binding.get("source"), None
        else:
            source, value = next(
                ((name, v) for name, v in available.items() if v is not None), (None, None)
            )

        fields[field] = {
            "value": _coerce(metadata, field, value),
            "source": source,
            # Whether the source was chosen or merely landed on, which is the
            # difference between a decision to leave a field empty and nobody
            # having filled it in yet.
            "bound": binding is not None,
            "available": available,
            # Carried through from the binding so that the interface has one place
            # to look for everything about a field.
            **{
                k: binding[k]
                for k in ("set_by", "set_by_name", "set_at")
                if binding and k in binding
            },
        }

    return MetadataResolution(metadata=metadata, fields=fields)
