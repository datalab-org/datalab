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
from pydatalab.blocks.metadata import (
    FileMetadata,
    FromFile,
    FromItem,
    _Gathered,
    metadata_entry,
    resolve_metadata,
)


class Metadata(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    sample_mass_mg: float | None = metadata_entry(
        FromFile("sample_mass_mg"), FromItem("sample_mass_mg")
    )
    molar_mass_g_mol: float | None = metadata_entry(
        FromFile("molar_mass_g_mol"), FromItem("molar_mass_g_mol")
    )
    comment: str | None = metadata_entry(FromFile("comment"), FromItem("comment"))

    @field_validator("sample_mass_mg", mode="after")
    @classmethod
    def _a_non_positive_mass_is_no_mass(cls, value):
        return None if value is not None and value <= 0 else value


FILE = {"sample_mass_mg": 14.32, "comment": "eicosane"}
SAMPLE = {"molar_mass_g_mol": 192.7}


def gathered(file=None, sample=None):
    return _Gathered(
        file=FileMetadata(name="measurement.dat", values=FILE if file is None else file),
        item_id="item-1",
        item=SAMPLE if sample is None else sample,
    )


def resolve(bindings=None, file=None, sample=None):
    return resolve_metadata(Metadata, gathered(file, sample), bindings)


def test_the_first_source_with_a_value_wins():
    resolution = resolve()

    assert resolution.metadata.sample_mass_mg == pytest.approx(14.32)
    assert resolution.fields["sample_mass_mg"]["source"] == "file"
    assert resolution.fields["molar_mass_g_mol"]["source"] == "item"


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
        "editable": True,
        "available": {"file": pytest.approx(14.32), "item": pytest.approx(21.0)},
        "labels": {"file": "measurement.dat", "item": "item-1"},
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
    resolution = resolve({"sample_mass_mg": {"source": "item"}}, sample={"sample_mass_mg": 21.0})

    assert resolution.metadata.sample_mass_mg == pytest.approx(21.0)
    assert resolution.fields["sample_mass_mg"]["source"] == "item"


def test_a_binding_whose_source_no_longer_has_the_value_leaves_it_empty():
    """Falling back would undo a choice somebody made, and do it silently."""
    resolution = resolve({"sample_mass_mg": {"source": "item"}})

    assert resolution.metadata.sample_mass_mg is None
    assert resolution.fields["sample_mass_mg"]["source"] == "item"


def test_an_unbound_field_changes_its_mind_when_a_better_source_appears():
    """The block guessed; a guess is made again rather than kept."""
    assert (
        resolve(sample={"comment": "from the sample"}, file={}).fields["comment"]["source"]
        == "item"
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

    def file_metadata(self):
        return FileMetadata(name="measurement.dat", values=FILE)

    def item_doc(self, projection):
        return SAMPLE


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


def test_a_source_is_named_after_the_file_and_the_item_it_came_from():
    """Which file a value came out of is the useful half of knowing it came from one,
    and core already knows both names, so no block has to say them."""
    labels = resolve().fields["molar_mass_g_mol"]["labels"]

    assert labels == {"file": "measurement.dat", "item": "item-1"}


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
        sample_mass_mg: float | None = metadata_entry(FromFile("sample_mass_mg"))

    junk = gathered(file={"sample_mass_mg": "heavy"})
    resolution = resolve_metadata(Unguarded, junk, None)
    # The file really did offer it -- otherwise the None below would prove nothing.
    assert junk.file.values["sample_mass_mg"] == "heavy"
    assert resolution.fields["sample_mass_mg"]["value"] is None

    # and a value still arrives as the type the model asks for
    typed = resolve_metadata(
        Unguarded, gathered(file={}), {"sample_mass_mg": {"source": "user", "value": "99"}}
    )
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

    class Plain(BaseModel):
        comment: str | None = None

    entry = entry_of(Plain.model_fields["comment"])
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


# --- Resolving from the declarations ---------------------------------------------


class Declared(BaseModel):
    wavelength: float | None = metadata_entry(FromFile("wavelength"), default=1.5406)
    count_time: float | None = metadata_entry(FromFile("count_time"))
    density: float | None = metadata_entry()


def test_the_default_is_tried_after_every_source():
    resolution = resolve_metadata(Declared, gathered(file={"wavelength": 0.7093}))
    assert resolution.metadata.wavelength == pytest.approx(0.7093)
    assert resolution.fields["wavelength"]["source"] == "file"

    fallback = resolve_metadata(Declared, gathered(file={}))
    assert fallback.metadata.wavelength == pytest.approx(1.5406)
    # Shown as a default, so it never passes for something measured.
    assert fallback.fields["wavelength"]["source"] == "default"
    assert fallback.fields["wavelength"]["labels"]["default"] == "default"


def test_a_field_without_a_default_offers_none():
    available = resolve_metadata(Declared, gathered(file={})).fields["count_time"]["available"]
    assert "default" not in available


def test_a_field_is_only_read_from_the_sources_it_names():
    """Leaving `FromItem` out means the item is never asked, even if it has the key."""
    resolution = resolve_metadata(
        Declared, gathered(file={}, sample={"count_time": 5.0, "density": 2.1})
    )

    assert resolution.metadata.count_time is None
    assert resolution.fields["density"]["available"] == {}, "entered by hand, and only that"


def test_the_item_is_asked_once_for_every_field_that_reads_from_it():
    projections = []

    class Counting(_Block):
        blocktype = "_metadata_test_counting"

        def item_doc(self, projection):
            projections.append(projection)
            return SAMPLE

    Counting(item_id="test").resolve_metadata()

    assert len(projections) == 1
    assert set(projections[0]) == {"sample_mass_mg", "molar_mass_g_mol", "comment"}


def test_a_block_with_no_field_reading_the_item_never_asks_it():
    class NoItem(DataBlock):
        blocktype = "_metadata_test_no_item"
        metadata_model = Declared

        def item_doc(self, projection):
            raise AssertionError("the item should not have been queried")

    NoItem(item_id="test").resolve_metadata()


def test_a_binding_names_one_of_the_sources_that_field_declares():
    """Sources are declared per field now, so "item" is a real source for a field
    that reads it, and not one for a field that does not."""
    block = _Block(item_id="test")
    block.process_events(
        {"event_name": "set_metadata_source", "field": "comment", "source": "item"}
    )
    assert block.data["metadata_bindings"]["comment"]["source"] == "item"

    class Defaulted(_Block):
        blocktype = "_metadata_test_defaulted"
        metadata_model = Declared

    for source, ok in (("default", True), ("item", False)):
        block = Defaulted(item_id="test")
        block.process_events(
            {"event_name": "set_metadata_source", "field": "wavelength", "source": source}
        )
        assert bool(block.data.get("errors")) is not ok, source


# --- Fields a person may not override --------------------------------------------


class ReadOnly(BaseModel):
    software: str | None = metadata_entry(FromFile("software"), editable=False)
    sample_mass_mg: float | None = metadata_entry(FromFile("sample_mass_mg"))


class _ReadOnlyBlock(DataBlock):
    blocktype = "_metadata_test_read_only"
    metadata_model = ReadOnly

    def file_metadata(self):
        return FileMetadata(name="measurement.dat", values={"software": "MultiVu 1.61"})


@pytest.mark.parametrize(
    "event",
    [
        {"source": "user", "value": "something else"},
        {"source": "user", "value": None},
        {"source": "file"},
    ],
)
def test_a_read_only_field_cannot_be_bound_to_anything(event):
    """A fact about the file -- the software that wrote it -- is not something to
    correct, and an override would muddy the provenance rather than clarify it."""
    block = _ReadOnlyBlock(item_id="test")
    block.process_events({"event_name": "set_metadata_source", "field": "software", **event})

    assert block.data["errors"]
    assert not block.data.get("metadata_bindings")


def test_a_binding_left_over_from_before_a_field_was_read_only_is_ignored():
    """Making a field read-only means its value follows the file from then on,
    including for blocks where somebody had overridden it beforehand."""
    block = _ReadOnlyBlock(item_id="test")
    block.data["metadata_bindings"] = {"software": {"source": "user", "value": "typed over"}}

    resolution = block.resolve_metadata()
    assert resolution.metadata.software == "MultiVu 1.61"
    assert resolution.fields["software"]["source"] == "file"
    assert resolution.fields["software"]["bound"] is False


def test_the_interface_is_told_which_fields_it_may_offer_to_change():
    fields = _ReadOnlyBlock(item_id="test").resolve_metadata().fields

    assert fields["software"]["editable"] is False
    assert fields["sample_mass_mg"]["editable"] is True
