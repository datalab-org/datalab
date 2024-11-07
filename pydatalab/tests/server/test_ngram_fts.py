"""This module tests fundamental routines around
the n-gram FTS.

"""

from pydatalab.mongo import _generate_item_ngrams, _generate_ngrams, create_ngram_item_index


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


def test_ngram_item():
    item = {"refcode": "ABCDEF"}
    assert _generate_item_ngrams(item, {"refcode"}, n=3) == {"abc": 1, "bcd": 1, "cde": 1, "def": 1}


def test_ngram_fts_route(client, default_sample_dict, real_mongo_client, database):
    default_sample_dict["item_id"] = "ABCDEF"
    response = client.post("/new-sample/", json=default_sample_dict)
    assert response.status_code == 201

    # Check that creating the ngram index with existing items works
    create_ngram_item_index(real_mongo_client, background=False, filter_top_ngrams=None)

    doc = database.items_fts.find_one({})
    ngrams = set(doc["_fts_ngrams"])
    for ng in ["abc", "bcd", "cde", "def", "sam", "ple"]:
        assert ng in ngrams
    assert doc["type"] == "samples"

    query_strings = ("ABC", "ABCDEF", "abcd", "cdef")

    for q in query_strings:
        response = client.get(f"/search-items-ngram/?query={q}&types=samples")
        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert len(response.json["items"]) == 1
        assert response.json["items"][0]["item_id"] == "ABCDEF"

    # Check that new items are added to the ngram index
    default_sample_dict["item_id"] = "ABCDEF2"
    response = client.post("/new-sample/", json=default_sample_dict)
    assert response.status_code == 201

    for q in query_strings:
        response = client.get(f"/search-items-ngram/?query={q}&types=samples")
        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert len(response.json["items"]) == 2
        assert response.json["items"][0]["item_id"] == "ABCDEF"
        assert response.json["items"][1]["item_id"] == "ABCDEF2"

    # Check that updates are reflected in the ngram index
    # This test also makes sure that the string 'test' is not picked up from the refcode,
    # which has an explicit carve out
    default_sample_dict["description"] = "test string with punctuation"
    update_req = {"item_id": "ABCDEF2", "data": default_sample_dict}
    response = client.post("/save-item/", json=update_req)
    assert response.status_code == 200

    query_strings = ("test", "punctuation")

    for q in query_strings:
        response = client.get(f"/search-items-ngram/?query={q}&types=samples")
        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert len(response.json["items"]) == 1
        assert response.json["items"][0]["item_id"] == "ABCDEF2"
