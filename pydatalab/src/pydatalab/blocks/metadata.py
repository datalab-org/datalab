# This file was edited with the assistance of an AI model and requires human review from the contributor.

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

from typing import Any, ClassVar, NamedTuple

from pydantic import BaseModel, Field
from pydantic_core import PydanticUndefined

__all__ = (
    "USER",
    "AUTO",
    "FromFile",
    "FromItem",
    "FileMetadata",
    "MetadataEntry",
    "MetadataResolution",
    "metadata_entry",
    "entry_of",
    "source_names",
    "resolve_metadata",
)

USER = "user"
"""The binding for a value the user gave, which is stored rather than re-read."""

AUTO = "auto"
"""Not a binding: asking for this clears one, putting the field back to guessing."""


class FileMetadata(NamedTuple):
    """What a block read from its file: the file's name, and its raw metadata."""

    name: str
    """Shown to a person as where a value came from."""

    values: dict[str, Any]
    """The raw key/value metadata, as `FromFile` looks keys up in it."""


class _Gathered(NamedTuple):
    """Everything the sources can read from, gathered once per resolution."""

    file: FileMetadata | None
    item_id: str | None
    item: dict[str, Any]


class MetadataSource:
    """Somewhere a metadata value can come from."""

    name: ClassVar[str]
    """The source's name in a binding, and in the interface."""

    def read(self, gathered: _Gathered) -> Any:
        raise NotImplementedError

    def label(self, gathered: _Gathered) -> str:
        """How to name this source to a person."""
        return self.name


class FromFile(MetadataSource):
    """Read from the block's file, under the first of these keys that holds a value.

    The keys are tried in order, so the spellings of one quantity across instrument
    generations can be listed together: `FromFile("SAMPLE_MASS", "WEIGHT")`.
    """

    name = "file"

    def __init__(self, *keys: str):
        if not keys:
            # Deliberately not "the field's own name": a field that silently looks
            # itself up under a key nobody wrote down is exactly the always-empty
            # field this is meant to make impossible.
            raise TypeError("FromFile needs at least one key to look up in the file.")
        self.keys = keys

    def read(self, gathered):
        if gathered.file is None:
            return None
        for key in self.keys:
            value = gathered.file.values.get(key)
            if value is not None and not (isinstance(value, str) and not value.strip()):
                return value
        return None

    def label(self, gathered):
        return gathered.file.name if gathered.file else self.name

    def __repr__(self):
        return f"FromFile({', '.join(map(repr, self.keys))})"


class FromItem(MetadataSource):
    """Read from the datalab item the block is attached to, e.g. the molar mass
    derived from a sample's chemical formula."""

    name = "item"

    def __init__(self, field: str):
        self.field = field

    def read(self, gathered):
        return gathered.item.get(self.field)

    def label(self, gathered):
        return gathered.item_id or self.name

    def __repr__(self):
        return f"FromItem({self.field!r})"


DEFAULT = "default"
"""The source name for a field's declared default, which is tried after all others."""


class MetadataEntry(NamedTuple):
    """Where one metadata field comes from, and whether a person may change it."""

    sources: tuple[MetadataSource, ...] = ()
    """Tried in order; the first with a value wins. Empty means only a person can
    supply the value."""

    editable: bool = True
    """Whether a person may override what the sources say. Worth turning off for a
    fact about the file -- the software that wrote it, say -- where an override
    would muddy the provenance rather than clarify it."""


def metadata_entry(
    *sources: MetadataSource, default: Any = None, editable: bool = True, **field_kwargs
) -> Any:
    """Declare a metadata field, and where its value comes from.

    Sources are given in priority order:

        sample_mass_mg: float | None = metadata_entry(FromFile("SAMPLE_MASS", "WEIGHT"))
        molar_mass_g_mol: float | None = metadata_entry(
            FromFile("SAMPLE_MOLECULAR_WEIGHT"), FromItem("molar_mass")
        )
        wavelength_angstrom: float | None = metadata_entry(FromFile("wavelength"), default=1.5406)
        density_g_cm3: float | None = metadata_entry()   # entered by hand

    Leaving a source out means the field is never read from it; giving none at all
    means a person has to enter it. The `default` is tried after every source --
    always last, which is what makes it a default -- and is shown as one, so that it
    never passes for a measurement. A value somebody has set wins over all of them,
    which is what an override is.

    Any other keyword is passed to pydantic's `Field`.
    """
    for source in sources:
        if not isinstance(source, MetadataSource):
            raise TypeError(f"{source!r} is not a metadata source, e.g. FromFile(...)")

    names = [source.name for source in sources]
    if len(names) != len(set(names)):
        raise TypeError(
            f"Sources {names} name the same source twice; give one source several "
            "keys instead, e.g. FromFile('SAMPLE_MASS', 'WEIGHT')."
        )

    if not sources and default is None and not editable:
        raise TypeError(
            "A field with no sources, no default, and nobody to edit it could only be empty."
        )

    field = Field(default, **field_kwargs)
    field.metadata.append(MetadataEntry(sources=sources, editable=editable))
    return field


def entry_of(field_info) -> MetadataEntry:
    """The entry declared on a field, or the default for a plain one: no sources,
    editable -- so a field without `metadata_entry` is one a person fills in."""
    return next(
        (marker for marker in field_info.metadata if isinstance(marker, MetadataEntry)),
        MetadataEntry(),
    )


class MetadataResolution(BaseModel):
    """The outcome of resolving one block's metadata."""

    metadata: BaseModel
    """The values in force, as the block's own metadata model."""

    fields: dict[str, dict[str, Any]]
    """Per field, the value, the source it came from, and what the other sources
    have to offer -- which is what lets the interface say where a number came from
    and offer the alternatives."""

    model_config = {"arbitrary_types_allowed": True}


def _coerce(model: type[BaseModel], field: str, value: Any) -> Any:
    """What the model makes of a value for one field, or None if it will not have it.

    Validated rather than assigned: a model only checks assignments if it asks to,
    and the guarantee here -- that a file is free to contain nonsense in a field
    nobody needs, and loses only that field by it -- should not depend on whether
    the block that wrote the model happened to think of that.
    """
    try:
        return getattr(model.model_validate({field: value}), field)
    except Exception:  # noqa: S110 -- a bad value is one missing value, not an error
        return None


def _default_of(field_info) -> Any:
    """A field's declared default, or None if it has none worth offering."""
    default = field_info.default
    return None if default is PydanticUndefined else default


def source_names(model: type[BaseModel], field: str) -> list[str]:
    """The sources a field may be bound to, in the order they are tried."""
    field_info = model.model_fields[field]
    names = [source.name for source in entry_of(field_info).sources]
    if _default_of(field_info) is not None:
        names.append(DEFAULT)
    return names


def resolve_metadata(
    model: type[BaseModel],
    gathered: _Gathered,
    bindings: dict[str, dict] | None = None,
) -> MetadataResolution:
    """Work out each field's value from its declared sources, and record where it
    came from.

    Args:
        model: The block's metadata model, whose fields declare their sources with
            `metadata_entry`. Every field must be optional.
        gathered: What the sources read from: the block's file and its item.
        bindings: The bindings the user has set, as `{field: {"source": ...}}`,
            carrying a `"value"` as well when the source is the user.

    """
    bindings = bindings or {}
    metadata = model()
    fields: dict[str, dict[str, Any]] = {}

    for field, field_info in model.model_fields.items():
        entry = entry_of(field_info)

        # Every declared source, in the order the field gives them, then its
        # default. All are read whether or not they win, so the interface can
        # offer each one by name.
        available: dict[str, Any] = {}
        labels: dict[str, str] = {}
        for declared in entry.sources:
            available[declared.name] = _coerce(model, field, declared.read(gathered))
            labels[declared.name] = declared.label(gathered)
        if (default := _default_of(field_info)) is not None:
            available[DEFAULT] = _coerce(model, field, default)
            labels[DEFAULT] = DEFAULT

        binding = bindings.get(field)
        if not isinstance(binding, dict) or not entry.editable:
            # Nothing readable, or a field nobody may override -- in which case a
            # binding stored before it was made read-only must not still apply.
            binding = None

        source: str | None
        value: Any
        if binding and binding.get("source") == USER:
            source, value = USER, binding.get("value")
        elif binding and binding.get("source") in available:
            source, value = binding["source"], available[binding["source"]]
        elif binding:
            # Bound to a source the field no longer has. Left empty rather than
            # quietly falling back, which would undo a choice somebody made.
            source, value = binding.get("source"), None
        else:
            source, value = next(
                ((name, v) for name, v in available.items() if v is not None), (None, None)
            )

        value = _coerce(model, field, value)
        setattr(metadata, field, value)
        fields[field] = {
            "value": value,
            "source": source,
            # Whether the source was chosen or merely landed on, which is the
            # difference between a decision to leave a field empty and nobody
            # having filled it in yet.
            "bound": binding is not None,
            "editable": entry.editable,
            "available": available,
            "labels": labels,
            # Carried through from the binding so that the interface has one place
            # to look for everything about a field.
            **{
                k: binding[k]
                for k in ("set_by", "set_by_name", "set_at")
                if binding and k in binding
            },
        }

    return MetadataResolution(metadata=metadata, fields=fields)
