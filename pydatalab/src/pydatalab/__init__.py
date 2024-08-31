from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("datalab-server")
except PackageNotFoundError:
    __version__ = "develop"
