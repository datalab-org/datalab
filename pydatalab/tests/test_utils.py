from pydatalab.utils.plotting import generate_unique_labels


def test_generate_unique_labels_single_file():
    result = generate_unique_labels(["sample_xrd_pattern.cif"])
    assert result == ["sample_xrd_pattern.cif"]


def test_generate_unique_labels_empty():
    result = generate_unique_labels([])
    assert result == []


def test_generate_unique_labels_common_suffix():
    filenames = ["sample1-xrd.xrdml", "sample2-xrd.xrdml"]
    result = generate_unique_labels(filenames)
    assert result == ["sample1.xrdml", "sample2.xrdml"]


def test_generate_unique_labels_prefix_and_suffix():
    filenames = [
        "experiment_run1_final.dat",
        "experiment_run2_final.dat",
        "experiment_run3_final.dat",
    ]
    result = generate_unique_labels(filenames)
    assert result == ["run1.dat", "run2.dat", "run3.dat"]


def test_generate_unique_labels_long_unique_parts():
    filenames = [
        "very_long_sample_name_with_many_characters_001.cif",
        "very_long_sample_name_with_many_characters_002.cif",
    ]
    result = generate_unique_labels(filenames, max_length=10)
    assert all(len(label) <= 15 for label in result)
    assert result[0] != result[1]


def test_generate_unique_labels_duplicates_after_shortening():
    filenames = [
        "CIF_0000000000000001.xrdml",
        "CIF_0000000000000002.xrdml",
    ]
    result = generate_unique_labels(filenames, max_length=15)
    assert result == ["CIF...1.xrdml", "CIF...2.xrdml"]


def test_generate_unique_labels_common_prefix():
    filenames = ["ICSDCollCode-000002.cif", "ICSDCollCode-000003.cif"]
    result = generate_unique_labels(filenames)
    assert result == ["ICSD...2.cif", "ICSD...3.cif"]


def test_generate_unique_labels_same_extension():
    filenames = ["sample_A.cif", "sample_B.cif", "sample_C.cif"]
    result = generate_unique_labels(filenames)
    assert result == ["sample_A.cif", "sample_B.cif", "sample_C.cif"]


def test_generate_unique_labels_cif_pattern():
    filenames = ["CIF_00000001.cif", "CIF_00000002.cif"]
    result = generate_unique_labels(filenames)
    assert result == ["CIF...1.cif", "CIF...2.cif"]
