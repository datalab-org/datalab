from pydatalab.routes.v0_1.items import extract_mentioned_items


def test_extract_single_cross_reference():
    """Test extraction of a single cross-reference."""
    html = (
        "<p>Related to "
        '<span data-item-id="test_sample" data-item-type="samples" '
        'data-name="Test" data-chemform="" data-type="crossreference"></span>'
        "</p>"
    )

    result = extract_mentioned_items(html)
    assert result == {"test_sample"}


def test_extract_multiple_cross_references():
    """Test extraction of multiple cross-references."""
    html = (
        "<p>Related to "
        '<span data-item-id="sample_1" data-item-type="samples" '
        'data-name="First" data-chemform="" data-type="crossreference"></span> and '
        '<span data-item-id="sample_2" data-item-type="samples" '
        'data-name="Second" data-chemform="" data-type="crossreference"></span>'
        "</p>"
    )

    result = extract_mentioned_items(html)
    assert result == {"sample_1", "sample_2"}


def test_extract_no_cross_references():
    """Test extraction when no cross-references exist."""
    html = "<p>Just plain text with no cross-references</p>"

    result = extract_mentioned_items(html)
    assert result == set()


def test_extract_empty_html():
    """Test extraction from empty HTML."""
    result = extract_mentioned_items("")
    assert result == set()


def test_extract_none_html():
    """Test extraction from None."""
    result = extract_mentioned_items(None)
    assert result == set()


def test_extract_with_different_attribute_order():
    """Test that extraction works regardless of attribute order."""
    html = (
        "<p>Test "
        '<span data-type="crossreference" data-chemform="" '
        'data-name="Test" data-item-type="samples" data-item-id="test_sample"></span>'
        "</p>"
    )

    result = extract_mentioned_items(html)
    assert result == {"test_sample"}


def test_extract_duplicate_references():
    """Test that duplicate references are handled correctly."""
    html = (
        "<p>First mention: "
        '<span data-item-id="sample_1" data-item-type="samples" '
        'data-type="crossreference"></span> second mention: '
        '<span data-item-id="sample_1" data-item-type="samples" '
        'data-type="crossreference"></span>'
        "</p>"
    )

    result = extract_mentioned_items(html)
    assert result == {"sample_1"}
