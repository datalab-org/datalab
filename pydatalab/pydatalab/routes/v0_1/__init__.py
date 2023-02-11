from typing import Callable, Dict

from ._version import __api_version__
from .auth import ENDPOINTS as auth_endpoints
from .blocks import ENDPOINTS as blocks_endpoints
from .collections import ENDPOINTS as collections_endpoints
from .files import ENDPOINTS as files_endpoints
from .graphs import ENDPOINTS as graphs_endpoints
from .healthcheck import ENDPOINTS as healthcheck_endpoints
from .info import ENDPOINTS as info_endpoints
from .items import ENDPOINTS as items_endpoints
from .remotes import ENDPOINTS as remotes_endpoints

ENDPOINTS: Dict[str, Callable] = {
    **blocks_endpoints,
    **items_endpoints,
    **files_endpoints,
    **remotes_endpoints,
    **healthcheck_endpoints,
    **auth_endpoints,
    **graphs_endpoints,
    **info_endpoints,
    **collections_endpoints,
}

__all__ = ("ENDPOINTS", "__api_version__")
