from typing import Callable, Dict

from ._version import __api_version__
from .auth import ENDPOINTS as auth_endpoints
from .blocks import ENDPOINTS as blocks_endpoints
from .collections import collection
from .files import ENDPOINTS as files_endpoints
from .graphs import ENDPOINTS as graphs_endpoints
from .healthcheck import ENDPOINTS as healthcheck_endpoints
from .info import ENDPOINTS as info_endpoints
from .items import ENDPOINTS as items_endpoints
from .remotes import remote

ENDPOINTS: Dict[str, Callable] = {
    **blocks_endpoints,
    **items_endpoints,
    **files_endpoints,
    **healthcheck_endpoints,
    **auth_endpoints,
    **graphs_endpoints,
    **info_endpoints,
}

BLUEPRINTS = [collection, remote]

__all__ = ("ENDPOINTS", "BLUEPRINTS", "__api_version__")
