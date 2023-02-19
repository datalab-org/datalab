from pathlib import Path


def test_tga_parse():

    from pydatalab.apps.tga import parse

    tga = parse(
        Path(__file__).parent.parent.parent
        / "example_data"
        / "TGA"
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

    expected_shape = (1366, 3)
    assert all(k in tga["data"] for k in expected_species)

    for k in expected_species:
        assert tga["data"][k].shape == expected_shape
