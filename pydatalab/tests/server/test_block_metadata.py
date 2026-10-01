# This file was edited with the assistance of an AI model and requires human review from the contributor.

"""Tests for metadata resolution and the bindings that decide it.

The rule these are all circling: the block's own choices stay open and are made
again on every render, so a value follows the file or the sample it came from;
the user's choices are kept, including the choice that a field should be empty.
"""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import BaseModel, ConfigDict, field_validator

from pydatalab.blocks.base import DataBlock
from pydatalab.blocks.metadata import resolve_metadata


class Metadata(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    sample_mass_mg: float | None = None
    molar_mass_g_mol: float | None = None
    comment: str | None = None

    @field_validator("sample_mass_mg", mode="after")
    @classmethod
    def _a_non_positive_mass_is_no_mass(cls, value):
        return None if value is not None and value <= 0 else value


FILE = {"sample_mass_mg": 14.32, "comment": "eicosane"}
SAMPLE = {"molar_mass_g_mol": 192.7}


def resolve(bindings=None, file=None, sample=None):
    return resolve_metadata(
        Metadata,
        {"file": FILE if file is None else file, "sample": SAMPLE if sample is None else sample},
        bindings,
    )


def test_the_first_source_with_a_value_wins():
    resolution = resolve()

    assert resolution.metadata.sample_mass_mg == pytest.approx(14.32)
    assert resolution.fields["sample_mass_mg"]["source"] == "file"
    assert resolution.fields["molar_mass_g_mol"]["source"] == "sample"


def test_a_field_no_source_has_is_empty_and_came_from_nowhere():
    resolution = resolve(file={}, sample={})

    assert resolution.metadata.comment is None
    assert resolution.fields["comment"]["source"] is None


def test_every_source_is_reported_not_only_the_winner():
    """The interface needs the alternatives to be able to offer them."""
    resolution = resolve(sample={"sample_mass_mg": 21.0})

    assert resolution.fields["sample_mass_mg"] == {
        "value": pytest.approx(14.32),
        "source": "file",
        "bound": False,
        "available": {"file": pytest.approx(14.32), "sample": pytest.approx(21.0)},
    }


def test_a_user_value_beats_every_source():
    resolution = resolve({"sample_mass_mg": {"source": "user", "value": 99.0}})

    assert resolution.metadata.sample_mass_mg == pytest.approx(99.0)
    assert resolution.fields["sample_mass_mg"]["source"] == "user"
    # and the file is still there to go back to
    assert resolution.fields["sample_mass_mg"]["available"]["file"] == pytest.approx(14.32)


def test_a_user_may_say_a_field_has_no_good_value():
    """Clearing a field is a decision, not the absence of one: the file is not
    consulted again on the next render."""
    resolution = resolve({"sample_mass_mg": {"source": "user", "value": None}})

    assert resolution.metadata.sample_mass_mg is None
    assert resolution.fields["sample_mass_mg"]["source"] == "user"


def test_which_is_not_the_same_as_never_having_chosen():
    """Both end up on the file's value; only one of them is a decision."""
    cleared = resolve({"sample_mass_mg": {"source": "user", "value": None}})
    untouched = resolve({})

    assert cleared.fields["sample_mass_mg"]["bound"] is True
    assert untouched.fields["sample_mass_mg"]["bound"] is False
    assert untouched.fields["sample_mass_mg"]["source"] == "file"


def test_a_zero_a_user_typed_is_kept_as_their_choice_even_where_it_is_no_value():
    """The model has nothing to do with a mass of zero, but the decision that this
    field is not to be filled from the file survives."""
    resolution = resolve({"sample_mass_mg": {"source": "user", "value": 0}})

    assert resolution.metadata.sample_mass_mg is None
    assert resolution.fields["sample_mass_mg"]["source"] == "user"


def test_a_bound_field_follows_its_source():
    """The point of binding rather than storing: re-uploading the file moves the
    value with it."""
    bindings = {"sample_mass_mg": {"source": "file"}}

    assert resolve(bindings).metadata.sample_mass_mg == pytest.approx(14.32)
    assert resolve(bindings, file={"sample_mass_mg": 21.4}).metadata.sample_mass_mg == (
        pytest.approx(21.4)
    )


def test_a_binding_can_pick_a_source_that_would_not_have_won():
    resolution = resolve({"sample_mass_mg": {"source": "sample"}}, sample={"sample_mass_mg": 21.0})

    assert resolution.metadata.sample_mass_mg == pytest.approx(21.0)
    assert resolution.fields["sample_mass_mg"]["source"] == "sample"


def test_a_binding_whose_source_no_longer_has_the_value_leaves_it_empty():
    """Falling back would undo a choice somebody made, and do it silently."""
    resolution = resolve({"sample_mass_mg": {"source": "sample"}})

    assert resolution.metadata.sample_mass_mg is None
    assert resolution.fields["sample_mass_mg"]["source"] == "sample"


def test_an_unbound_field_changes_its_mind_when_a_better_source_appears():
    """The block guessed; a guess is made again rather than kept."""
    assert (
        resolve(sample={"comment": "from the sample"}, file={}).fields["comment"]["source"]
        == "sample"
    )
    assert resolve(sample={"comment": "from the sample"}).fields["comment"]["source"] == "file"


def test_a_source_holding_nonsense_costs_that_field_and_nothing_else():
    """A file is free to contain rubbish in a field nobody needs."""
    resolution = resolve(file={"sample_mass_mg": "heavy", "comment": "fine"})

    assert resolution.fields["sample_mass_mg"]["value"] is None
    assert resolution.metadata.comment == "fine"


class _Block(DataBlock):
    blocktype = "_metadata_test"
    metadata_model = Metadata

    def metadata_sources(self):
        return {"file": FILE, "sample": SAMPLE}


def test_the_event_records_a_binding_and_resolution_honours_it():
    block = _Block(item_id="test")
    block.process_events(
        {
            "event_name": "set_metadata_source",
            "field": "sample_mass_mg",
            "source": "user",
            "value": "99",
        }
    )

    binding = block.data["metadata_bindings"]["sample_mass_mg"]
    assert binding["source"] == "user"
    assert binding["value"] == "99"
    assert block.resolve_metadata().metadata.sample_mass_mg == pytest.approx(99.0)


def test_a_binding_records_when_it_was_made():
    """Somebody deciding a value should not be worked out the usual way is worth
    being able to attribute afterwards."""
    block = _Block(item_id="test")
    block.process_events(
        {
            "event_name": "set_metadata_source",
            "field": "sample_mass_mg",
            "source": "user",
            "value": "99",
        }
    )

    stamped = datetime.fromisoformat(block.data["metadata_bindings"]["sample_mass_mg"]["set_at"])
    assert stamped.tzinfo is not None
    assert abs((datetime.now(tz=timezone.utc) - stamped).total_seconds()) < 60

    # and it reaches the interface alongside the value it belongs to
    assert block.resolve_metadata().fields["sample_mass_mg"]["set_at"]


def test_a_binding_records_who_made_it(monkeypatch):
    from bson import ObjectId

    from pydatalab.blocks import base

    person = SimpleNamespace(immutable_id=ObjectId("1" * 24), display_name="Ada Lovelace")
    monkeypatch.setattr(base, "has_request_context", lambda: True)
    monkeypatch.setattr(base, "current_user", SimpleNamespace(person=person))

    block = _Block(item_id="test")
    block.process_events(
        {
            "event_name": "set_metadata_source",
            "field": "sample_mass_mg",
            "source": "user",
            "value": "99",
        }
    )

    binding = block.data["metadata_bindings"]["sample_mass_mg"]
    assert binding["set_by"] == "1" * 24
    assert binding["set_by_name"] == "Ada Lovelace"

    # Choosing which source to take a value from is a decision too, so it is
    # attributed the same way.
    block.process_events(
        {"event_name": "set_metadata_source", "field": "sample_mass_mg", "source": "file"}
    )
    assert block.data["metadata_bindings"]["sample_mass_mg"]["set_by_name"] == "Ada Lovelace"

    assert block.resolve_metadata().fields["sample_mass_mg"]["set_by_name"] == "Ada Lovelace"


def test_there_is_nobody_to_name_outside_a_request():
    """Which must not be an error: the tests, and any script, resolve blocks with
    no user logged in."""
    block = _Block(item_id="test")
    block.process_events(
        {
            "event_name": "set_metadata_source",
            "field": "sample_mass_mg",
            "source": "user",
            "value": "99",
        }
    )

    assert not block.data.get("errors")
    assert "set_by" not in block.data["metadata_bindings"]["sample_mass_mg"]


def test_asking_for_auto_drops_the_binding():
    block = _Block(item_id="test")
    block.data["metadata_bindings"] = {"sample_mass_mg": {"source": "user", "value": 99.0}}
    block.process_events(
        {"event_name": "set_metadata_source", "field": "sample_mass_mg", "source": "auto"}
    )

    assert block.data["metadata_bindings"] == {}
    assert block.resolve_metadata().fields["sample_mass_mg"]["source"] == "file"


@pytest.mark.parametrize(
    "event",
    [
        {"field": "not_a_field", "source": "user", "value": 1},
        {"field": "sample_mass_mg", "source": "not_a_source"},
    ],
)
def test_an_impossible_binding_becomes_a_block_error(event):
    block = _Block(item_id="test")
    block.process_events({"event_name": "set_metadata_source", **event})

    assert block.data["errors"]
    assert not block.data.get("metadata_bindings")


def test_a_block_may_say_what_its_sources_should_be_called():
    """ "file" is not much use on its own; which file is the useful half."""

    class Named(_Block):
        blocktype = "_metadata_test_named"

        def metadata_source_labels(self):
            return {"file": "measurement.dat"}

    block = Named(item_id="test")
    block.resolve_metadata()

    assert block.data["metadata_source_labels"] == {"file": "measurement.dat"}


def test_an_event_that_failed_is_still_reported_after_a_plot_that_did_not():
    """`to_web` rebuilds the block's errors from what the plots say, so an event
    that failed on the way there used to disappear -- leaving a control that did
    nothing and said nothing about why."""

    class Plotting(_Block):
        blocktype = "_metadata_test_plotting"

        @property
        def plot_functions(self):
            return (lambda: None,)

    block = Plotting(item_id="test")
    block.process_events(
        {"event_name": "set_metadata_source", "field": "nope", "source": "user", "value": 1}
    )

    assert block.to_web()["errors"]


def test_a_model_that_does_not_validate_assignments_is_still_protected():
    """The guarantee that a file may contain nonsense and lose only that field must
    not depend on the block having thought to enable assignment validation."""

    class Unguarded(BaseModel):
        sample_mass_mg: float | None = None

    resolution = resolve_metadata(Unguarded, {"file": {"sample_mass_mg": "heavy"}}, None)
    assert resolution.fields["sample_mass_mg"]["value"] is None

    # and a value still arrives as the type the model asks for
    typed = resolve_metadata(Unguarded, {}, {"sample_mass_mg": {"source": "user", "value": "99"}})
    assert typed.metadata.sample_mass_mg == pytest.approx(99.0)


def test_a_binding_that_is_not_a_binding_costs_that_field_and_nothing_else():
    """Bindings come from the database, which has held other shapes before now."""
    resolution = resolve(bindings={"sample_mass_mg": "nonsense"})

    assert resolution.metadata.sample_mass_mg == pytest.approx(14.32)
    assert resolution.fields["sample_mass_mg"]["bound"] is False


def test_the_web_cannot_write_a_binding_directly():
    """A binding says who chose a value and when. Letting the web set one would be
    letting it make a claim about a person that nobody checked."""
    schema = DataBlock.block_db_model.model_json_schema()["properties"]
    assert schema["metadata_bindings"]["datalab_exclude_from_load"]


def test_a_source_may_not_be_called_user_or_auto():
    """Those are the two answers the event gives itself, so a source of either name
    could never be bound to -- and asking for it would blank the field instead."""

    class Colliding(_Block):
        blocktype = "_metadata_test_colliding"

        def metadata_sources(self):
            return {"user": {"sample_mass_mg": 1.0}}

    block = Colliding(item_id="test")
    block.process_events(
        {"event_name": "set_metadata_source", "field": "sample_mass_mg", "source": "user"}
    )

    assert block.data["errors"]
    assert not block.data.get("metadata_bindings")


def test_setting_a_source_resolves_there_and_then():
    """`to_web` only runs the plot functions, so a block whose plots do not resolve
    would answer the request with the value the field had before the choice."""
    block = _Block(item_id="test")
    block.resolve_metadata()
    block.process_events(
        {
            "event_name": "set_metadata_source",
            "field": "sample_mass_mg",
            "source": "user",
            "value": 99,
        }
    )

    assert block.data["metadata"]["sample_mass_mg"] == pytest.approx(99.0)
    assert block.data["metadata_fields"]["sample_mass_mg"]["source"] == "user"


def test_resolving_writes_both_the_values_and_their_provenance():
    block = _Block(item_id="test")
    block.resolve_metadata()

    assert block.data["metadata"]["sample_mass_mg"] == pytest.approx(14.32)
    assert block.data["metadata_fields"]["sample_mass_mg"]["source"] == "file"


# --- Declaring where a field comes from ------------------------------------------


def test_a_declared_field_keeps_its_sources_its_label_and_its_default():
    from pydatalab.blocks.metadata import FromFile, FromItem, entry_of, metadata_entry

    class Declared(BaseModel):
        model_config = ConfigDict(use_attribute_docstrings=True)

        molar_mass_g_mol: float | None = metadata_entry(
            FromFile("SAMPLE_MOLECULAR_WEIGHT"), FromItem("molar_mass")
        )
        """Molar mass (g/mol)."""

        wavelength: float | None = metadata_entry(FromFile("wavelength"), default=1.5406)

    entry = entry_of(Declared.model_fields["molar_mass_g_mol"])
    assert [source.name for source in entry.sources] == ["file", "item"]
    assert entry.editable

    # It is still an ordinary pydantic field in every other respect.
    assert Declared.model_fields["molar_mass_g_mol"].description == "Molar mass (g/mol)."
    assert Declared().wavelength == pytest.approx(1.5406)
    assert Declared(molar_mass_g_mol="58.4").molar_mass_g_mol == pytest.approx(58.4)
    assert "molar_mass_g_mol" in Declared.model_json_schema()["properties"]


def test_a_plain_field_is_one_a_person_fills_in():
    from pydatalab.blocks.metadata import entry_of

    entry = entry_of(Metadata.model_fields["comment"])
    assert entry.sources == ()
    assert entry.editable


def test_file_needs_to_be_told_which_key_to_read():
    """Not "the field's own name": a field that quietly looks itself up under a key
    nobody wrote down is the always-empty field this is meant to rule out."""
    from pydatalab.blocks.metadata import FromFile

    with pytest.raises(TypeError, match="at least one key"):
        FromFile()


def test_a_source_is_something_that_says_where_a_value_comes_from():
    from pydatalab.blocks.metadata import metadata_entry

    with pytest.raises(TypeError, match="not a metadata source"):
        metadata_entry("SAMPLE_MASS")


def test_naming_one_source_twice_is_a_mistake_rather_than_a_fallback():
    """Two FromFile entries would make "bind this to the file" ambiguous; one with
    several keys says the same thing without that problem."""
    from pydatalab.blocks.metadata import FromFile, metadata_entry

    with pytest.raises(TypeError, match="several keys"):
        metadata_entry(FromFile("A"), FromFile("B"))


def test_a_field_that_could_only_ever_be_empty_is_refused():
    from pydatalab.blocks.metadata import metadata_entry

    with pytest.raises(TypeError, match="could only be empty"):
        metadata_entry(editable=False)

    # A constant is pointless but not empty, so that much is allowed.
    metadata_entry(default=1.0, editable=False)


def test_file_takes_the_first_key_that_holds_a_value():
    """Newer headers write an unset field as a blank, so a blank is skipped rather
    than shadowing the spelling an older instrument used."""
    from pydatalab.blocks.metadata import FileMetadata, FromFile, _Gathered

    source = FromFile("SAMPLE_MASS", "WEIGHT")
    gathered = lambda values: _Gathered(  # noqa: E731
        file=FileMetadata(name="measurement.dat", values=values), item_id=None, item={}
    )

    assert source.read(gathered({"SAMPLE_MASS": "14.3", "WEIGHT": "9"})) == "14.3"
    assert source.read(gathered({"SAMPLE_MASS": "  ", "WEIGHT": "9"})) == "9"
    assert source.read(gathered({})) is None
    assert source.label(gathered({})) == "measurement.dat"
