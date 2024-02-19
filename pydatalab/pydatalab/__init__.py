from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pydatalab")
except PackageNotFoundError:
    __version__ = "develop"
