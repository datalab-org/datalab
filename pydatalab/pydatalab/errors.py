import traceback
from typing import Any, Callable, Iterable, Tuple

from flask import Response, jsonify
from werkzeug.exceptions import Forbidden, HTTPException

from pydatalab.config import CONFIG


class UserRegistrationForbidden(Forbidden):
    """Raised when a user tries to register via OAuth without the appropriate
    properties/credentials, e.g., public membership of a GitHub organization
    that is on the allow list.
    """

    description: str = """<html><head></head>
    <body>
    <h1>403 Forbidden</h1>

<h2>Unable to create account</h2>

<p>No user data will be stored as a result of this interaction, but you may wish to clear your cookies for this site.</p>

<p>
The OAuth identity used for registration is not on the allow list.
If you believe this to be an error, please first verify that your membership of the allowed
group (e.g., a GitHub organization) is public, and verify with the deployment manager that
the organization is indeed on the allow list.
</p>

<p>If this was not an error, you may wish to revoke any permissions given to the datalab OAuth application.</p>
</body>
</html>
"""


def handle_http_exception(exc: HTTPException) -> Tuple[Response, int]:
    """Return a specific error message and status code if the exception stores them."""
    response = {
        "title": exc.__class__.__name__,
        "description": exc.description,
    }
    status_code = exc.code if exc.code else 400

    return jsonify(response), status_code


def render_unauthorised_user_template(exc: UserRegistrationForbidden) -> Tuple[Response, int]:
    """Return a rich HTML page on user account creation failure."""
    return Response(response=exc.description), exc.code


def handle_generic_exception(exc: Exception) -> Tuple[Response, int]:
    """Return a specific error message and status code if the exception stores them."""
    if CONFIG.DEBUG:
        raise (exc)

    response = {
        "title": exc.__class__.__name__,
        "description": exc.args[0] if exc.args else "",
        # Return the full traceback under the key 'detail':
        "detail": "".join(traceback.format_exc()).replace("\n", "\\n"),
    }
    return jsonify(response), 500


ERROR_HANDLERS: Iterable[Tuple[Any, Callable[[Any], Tuple[Response, int]]]] = [
    (UserRegistrationForbidden, render_unauthorised_user_template),
    (HTTPException, handle_http_exception),
    (Exception, handle_generic_exception),
]
