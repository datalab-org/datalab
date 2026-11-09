"""Griffe extensions used when building the documentation.

`griffe-pydantic` recognises models by looking for `pydantic.BaseModel` among a
class's bases, falling back to the statically resolved MRO. That fails for
`ServerConfig`, which inherits from `BaseSettings`: pydantic ships compiled
modules, so griffe cannot parse them and the resolved MRO comes back empty.
The result is that `Field(..., description=...)` is never picked up and the
field renders as a raw `Field(...)` call expression instead of prose.

This extension teaches the check about the settings base classes for both
pydantic v1 (`pydantic.BaseSettings`) and v2 (`pydantic_settings.BaseSettings`),
so the docs keep working across the v2 migration.

It also drops validator methods from the rendered models. Validators are an
implementation detail of a model rather than part of its public schema, and
rendering one section per validator buries the fields the page is actually
about. They are identified by the `pydantic-validator` label that
`griffe-pydantic` attaches, rather than by name, since validator names follow no
consistent convention.
"""

from typing import Any

from griffe import Class, Expr, Module, Object
from griffe_pydantic import PydanticExtension
from griffe_pydantic._internal import static

SETTINGS_BASES = {
    # pydantic v1
    "pydantic.BaseSettings",
    "pydantic.env_settings.BaseSettings",
    # pydantic v2, via the separate pydantic-settings package
    "pydantic_settings.BaseSettings",
    "pydantic_settings.main.BaseSettings",
}

VALIDATOR_DECORATORS = {
    # pydantic v1
    "pydantic.validator",
    "pydantic.root_validator",
    # pydantic v2
    "pydantic.field_validator",
    "pydantic.model_validator",
}


class PydanticSettingsExtension(PydanticExtension):
    """`PydanticExtension` that also treats `BaseSettings` subclasses as models."""

    def on_package(self, *, pkg: Module, **kwargs: Any) -> None:
        original = static._inherits_pydantic

        def _inherits_pydantic(cls: Class) -> bool:
            for base in cls.bases:
                path = base.canonical_path if isinstance(base, Expr) else str(base)
                if path in SETTINGS_BASES:
                    return True
            return original(cls)

        # Patch only for the duration of the package pass, so that the override
        # cannot leak into unrelated griffe consumers.
        static._inherits_pydantic = _inherits_pydantic
        try:
            super().on_package(pkg=pkg, **kwargs)
        finally:
            static._inherits_pydantic = original

        _drop_validators(pkg)


def _is_validator(member: Any) -> bool:
    """Tell whether a member is a Pydantic validator.

    `griffe-pydantic` only labels the v2 decorators, so fall back to matching the
    decorator path directly, which also covers the v1 names still in use here.
    """
    if "pydantic-validator" in getattr(member, "labels", ()):
        return True
    return any(
        decorator.callable_path in VALIDATOR_DECORATORS
        for decorator in getattr(member, "decorators", ())
    )


def _drop_validators(obj: Object) -> None:
    """Recursively remove validator methods from Pydantic models."""
    if isinstance(obj, Class):
        for name in [name for name, member in obj.members.items() if _is_validator(member)]:
            del obj.members[name]

    for member in list(obj.members.values()):
        if isinstance(member, Object):
            _drop_validators(member)
