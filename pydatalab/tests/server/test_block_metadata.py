"""Tests for metadata resolution and the bindings that decide it.

The rule these are all circling: the block's own choices stay open and are made
again on every render, so a value follows the file or the sample it came from;
the user's choices are kept, including the choice that a field should be empty.
"""

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

    assert block.data["metadata_bindings"] == {"sample_mass_mg": {"source": "user", "value": "99"}}
    assert block.resolve_metadata().metadata.sample_mass_mg == pytest.approx(99.0)


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


def test_resolving_writes_both_the_values_and_their_provenance():
    block = _Block(item_id="test")
    block.resolve_metadata()

    assert block.data["metadata"]["sample_mass_mg"] == pytest.approx(14.32)
    assert block.data["metadata_fields"]["sample_mass_mg"]["source"] == "file"
