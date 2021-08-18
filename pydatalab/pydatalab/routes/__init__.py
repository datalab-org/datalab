from typing import Callable, Dict

from pydatalab.routes.blocks import ENDPOINTS as blocks_endpoints
from pydatalab.routes.files import ENDPOINTS as files_endpoints
from pydatalab.routes.remotes import ENDPOINTS as remotes_endpoints
from pydatalab.routes.samples import ENDPOINTS as samples_endpoints

ENDPOINTS: Dict[str, Callable] = {
    **blocks_endpoints,
    **samples_endpoints,
    **files_endpoints,
    **remotes_endpoints,
}
