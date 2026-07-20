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


def test_ms_parse_txt_with_validation():
    filename = (
        Path(__file__).parent.parent.parent / "example_data" / "TGA-MS" / "mp2028_281122_LNO+C.txt"
    )
    from pydatalab.apps.tga.parsers import parse_mt_mass_spec_txt

    ms = parse_mt_mass_spec_txt(filename)
    # check that the results exist
    assert ms

    assert "Performed" in ms["meta"]
    assert "t[s]" in ms["data"]["tga"]
    assert "Value[mg]" in ms["data"]["tga"]
    assert "Ts[°C]" in ms["data"]["tga"]
    assert "Tr[°C]" in ms["data"]["tga"]

    # regression test to check if means and standard deviations remain the same in the future
    assert pytest.approx(ms["data"]["tga"]["t[s]"].mean(), rel=1e-3) == 2025
    assert pytest.approx(ms["data"]["tga"]["t[s]"].std(), rel=1e-3) == 1169.57

    assert pytest.approx(ms["data"]["tga"]["Ts[°C]"].mean(), rel=1e-3) == 352.45
    assert pytest.approx(ms["data"]["tga"]["Ts[°C]"].std(), rel=1e-3) == 196.34

    assert pytest.approx(ms["data"]["tga"]["Tr[°C]"].mean(), rel=1e-3) == 362.45
    assert pytest.approx(ms["data"]["tga"]["Tr[°C]"].std(), rel=1e-3) == 194.93

    assert pytest.approx(ms["data"]["tga"]["Value[mg]"].mean(), rel=1e-3) == 4.16899
    assert pytest.approx(ms["data"]["tga"]["Value[mg]"].std(), rel=1e-3) == 0.004453
