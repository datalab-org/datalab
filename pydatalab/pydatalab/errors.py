import traceback
import os
from typing import Any, Callable, Iterable, Tuple

from flask import Response, jsonify
from pydantic import ValidationError
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

def handle_pydantic_validation_error(exc: ValidationError) -> Tuple[Response, int]:
    """Handle pydantic validation errors separately from other exceptions.
    These always come from malformed data, so should not necessarily trigger the
    Flask debugger.
    """
    response = {
        "title": exc.__class__.__name__,
        "message": str(exc.args[:]) if exc.args else "",
    }
    return jsonify(response), 500


def handle_generic_exception(exc: Exception) -> Tuple[Response, int]:
    """Return a specific error message and status code if the exception stores them."""
    if os.environ.get("FLASK_ENV") == "development":
        raise exc

    response = {
        "title": exc.__class__.__name__,
        "message": str(exc.args) if exc.args else "",
    }
    return jsonify(response), 500


ERROR_HANDLERS: Iterable[Tuple[Any, Callable[[Any], Tuple[Response, int]]]] = [
    (UserRegistrationForbidden, render_unauthorised_user_template),
    (HTTPException, handle_http_exception),
    (ValidationError, handle_pydantic_validation_error),
    (Exception, handle_generic_exception),
]
