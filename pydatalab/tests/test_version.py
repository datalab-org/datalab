def test_version():
    from pydatalab import __version__

    assert isinstance(__version__, str)
    assert int(__version__.split(".")[0]) == 0
    assert int(__version__.split(".")[1]) >= 4
