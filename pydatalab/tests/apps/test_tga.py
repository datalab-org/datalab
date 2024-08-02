from pathlib import Path

import pytest


def test_ms_parse_and_plot():
    from pydatalab.apps.tga.blocks import MassSpecBlock
    from pydatalab.apps.tga.parsers import parse_mt_mass_spec_ascii

    ms = parse_mt_mass_spec_ascii(
        Path(__file__).parent.parent.parent
        / "example_data"
        / "TGA-MS"
        / "20221128 134958 TGA MS Megan.asc"
    )

    expected_species = (
        "14",
        "16",
        "Water",
        "Nitrogen/Carbonmonoxide",
        "Oxygen",
        "Argon",
        "Carbondioxide",
    )

    # the final 3 columns are missing in the example file
    expected_shapes = [
        (1366, 2),
        (1366, 2),
        (1366, 2),
        (1365, 2),
        (1365, 2),
        (1365, 2),
        (1365, 2),
    ]

    assert all(k in ms["data"] for k in expected_species)

    for ind, k in enumerate(expected_species):
        assert ms["data"][k].shape == expected_shapes[ind]

    assert all(k in ms["meta"] for k in ("Start Time", "End Time", "Sourcefile", "Exporttime"))

    assert MassSpecBlock._plot_ms_data(ms)


@pytest.mark.parametrize(
    "filename", (Path(__file__).parent.parent.parent / "example_data" / "TGA-MS").glob("*.asc")
)
def test_ms_parse_no_validation(filename):
    from pydatalab.apps.tga.parsers import parse_mt_mass_spec_ascii

    ms = parse_mt_mass_spec_ascii(filename)
    assert ms

    assert all(k in ms["meta"] for k in ("Start Time", "End Time", "Sourcefile", "Exporttime"))

    for species in ms["data"]:
        assert (
            "Ion Current [A]" in ms["data"][species]
            or "Partial Pressure [mbar]" in ms["data"][species]
        )
        assert "Time Relative [s]" in ms["data"][species]
        assert "Time" not in ms["data"][species]
