"""This module tests fundamental routines around
the n-gram FTS.

"""

from pydatalab.mongo import _generate_item_ngrams, _generate_ngrams


def test_ngram_single_field():
    field = "ABCDEF"
    ngrams = _generate_ngrams(field, 3)
    expected = ["abc", "bcd", "cde", "def"]
    assert list(ngrams) == expected
    assert all([ngrams[e] == 1 for e in expected])

    field = "ABC"
    ngrams = _generate_ngrams(field, 3)
    assert ngrams == {"abc": 1}

    field = "some: punctuation"
    ngrams = _generate_ngrams(field, 3)
    expected = ["som", "ome", "pun", "unc", "nct", "ctu", "tua", "uat", "ati", "tio", "ion"]
    assert list(ngrams) == expected

    field = "What about a full sentence? or: even, two?"
    ngrams = _generate_ngrams(field, 3)
    expected = [
        "wha",
        "hat",
        "abo",
        "bou",
        "out",
        "ful",
        "ull",
        "sen",
        "ent",
        "nte",
        "ten",
        "enc",
        "nce",
        "eve",
        "ven",
        "two",
    ]
    assert list(ngrams) == expected
    assert all([ngrams[e] == 1 for e in expected])


def test_ngram_item(default):
    item = {"refcode": "ABCDEF"}
    assert _generate_item_ngrams(item, 3) == {"abc": 1, "bcd": 1, "cde": 1, "def": 1}
