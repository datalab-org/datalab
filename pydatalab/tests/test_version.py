def test_version():
    from pydatalab import __version__

    assert isinstance(__version__, str)
    assert int(__version__.split(".")[0]) == 0
    assert int(__version__.split(".")[1]) >= 4


def test_bokehjs_version_matches_python_bokeh():
    """BokehJS deserialises the plot JSON emitted by the Python `bokeh` package, so the
    two must be kept on the same version. They live in separate dependency files
    (`pydatalab/pyproject.toml` and `webapp/package.json`) and nothing else couples them,
    hence this check.
    """
    import json
    from pathlib import Path

    import bokeh
    import pytest

    package_json = Path(__file__).parent.parent.parent / "webapp" / "package.json"
    if not package_json.exists():
        pytest.skip("webapp/package.json not available in this checkout")

    bokehjs_version = json.loads(package_json.read_text())["dependencies"]["@bokeh/bokehjs"]

    assert bokehjs_version == bokeh.__version__, (
        f"BokehJS ({bokehjs_version}) and Python bokeh ({bokeh.__version__}) are out of sync; "
        "update webapp/package.json and pydatalab/pyproject.toml together."
    )
