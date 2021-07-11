def test_version():
    from pydatalab import __version__

    assert isinstance(__version__, str)
