from flask import Blueprint

from ._version import __api_version__
from .admin import ADMIN
from .auth import AUTH, OAUTH, OAUTH_PROXIES
from .blocks import BLOCKS
from .collections import COLLECTIONS
from .files import FILES
from .graphs import GRAPHS
from .healthcheck import HEALTHCHECK
from .info import INFO
from .items import ITEMS
from .remotes import REMOTES
from .users import USERS

BLUEPRINTS: tuple[Blueprint, ...] = (
    AUTH,
    COLLECTIONS,
    REMOTES,
    USERS,
    ADMIN,
    ITEMS,
    BLOCKS,
    FILES,
    HEALTHCHECK,
    INFO,
    GRAPHS,
)

__all__ = ("BLUEPRINTS", "OAUTH", "__api_version__", "OAUTH_PROXIES")
