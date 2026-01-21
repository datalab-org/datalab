from functools import wraps
from hashlib import sha512
from typing import Any

from bson import ObjectId
from flask import request
from flask_login import current_user

from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER
from pydatalab.login import UserRole
from pydatalab.models.people import AccountStatus
from pydatalab.mongo import flask_mongo, get_database

PUBLIC_USER_ID = ObjectId(24 * "0")


def active_users_or_get_only(func):
    """Decorator to ensure that only active user accounts can access the route,
    unless it is a GET-route, in which case deactivated accounts can also access it.
    Now also allows access with valid access tokens.
    """

    @wraps(func)
    def wrapped_route(*args, **kwargs):
        access_token = request.args.get("at")
        refcode = kwargs.get("refcode")

        if not refcode and access_token:
            path_parts = request.path.strip("/").split("/")
            if len(path_parts) >= 2 and path_parts[0] == "items":
                refcode = path_parts[1]

        if access_token and refcode:
            token_valid = check_access_token(refcode, access_token)
            if token_valid:
                return func(*args, **kwargs)

        if (
            (
                current_user.is_authenticated
                and (
                    current_user.account_status == AccountStatus.ACTIVE
                    or request.method in ("OPTIONS", "GET")
                )
            )
            or CONFIG.TESTING
            or request.method in ("OPTIONS",)
        ):
            return func(*args, **kwargs)

        return {"error": "Unauthorized"}, 401

    return wrapped_route


def access_token_or_active_users(func):
    """Decorator that checks for access tokens first, then falls back to normal authentication.
    If an access token is provided but invalid, the request is rejected regardless of normal permissions.
    """

    @wraps(func)
    def wrapped_route(*args, **kwargs):
        access_token = request.args.get("at")
        refcode = kwargs.get("refcode")

        if not refcode and access_token:
            path_parts = request.path.strip("/").split("/")
            if len(path_parts) >= 2 and path_parts[0] == "items":
                refcode = path_parts[1]

        if access_token:
            if refcode and check_access_token(refcode, access_token):
                return func(*args, elevate_permissions=True, **kwargs)
            else:
                return {"error": "Invalid access token"}, 401

        if (
            (
                current_user.is_authenticated
                and (
                    current_user.account_status == AccountStatus.ACTIVE
                    or request.method in ("OPTIONS", "GET")
                )
            )
            or CONFIG.TESTING
            or request.method in ("OPTIONS",)
        ):
            return func(*args, elevate_permissions=False, **kwargs)

        return {"error": "Unauthorized"}, 401

    return wrapped_route


def admin_only(func):
    """Decorator to ensure that only admin user accounts can access a route."""

    @wraps(func)
    def wrapped_route(*args, **kwargs):
        if (
            current_user.is_authenticated
            and current_user.role == UserRole.ADMIN
            and current_user.account_status == AccountStatus.ACTIVE
        ) or request.method in ("OPTIONS",):
            return func(*args, **kwargs)

        if not current_user.is_authenticated:
            return {"error": "Unauthorized"}, 401

        return {"error": "Insufficient privileges"}, 403

    return wrapped_route


def check_access_token(refcode: str, token: str | None = None) -> bool:
    """Check whether the provided access token exists in the get_database
    and corresponds to the relevant refcode.

    Returns:
        Whether or not the token can read the item.

    """

    if not token or not refcode:
        return False

    try:
        if len(refcode.split(":")) != 2:
            refcode = f"{CONFIG.IDENTIFIER_PREFIX}:{refcode}"

        token_hash = sha512(token.encode("utf-8")).hexdigest()

        access_token_doc = flask_mongo.db.api_keys.find_one(
            {"token": token_hash, "refcode": refcode, "active": True, "type": "access_token"}
        )

        if access_token_doc and access_token_doc["expires_at"] is not None:
            raise NotImplementedError("Token expiration is not yet implemented")

        return bool(access_token_doc)

    except Exception:
        return False


def get_default_permissions(
    user_only: bool = True, deleting: bool = False, elevate_permissions: bool = False
) -> dict[str, Any]:
    """Return the MongoDB query terms corresponding to the current user.

    Will return open permissions if a) the `CONFIG.TESTING` parameter is `True`,
    or b) if the current user is registered as an admin.

    Parameters:
        user_only: Whether to exclude items that also have no attached user (`False`),
            i.e., public items. This should be set to `False` when reading (and wanting
            to return public items), but left as `True` when modifying or removing items.
        elevate_permissions: Whether to elevate this query's permissions, i.e., in the case
            that an item-specific access token has been provided elsewhere.

    """

    if CONFIG.TESTING:
        return {}

    if (
        current_user.is_authenticated
        and current_user.person is not None
        and current_user.account_status == AccountStatus.ACTIVE
        and current_user.role == UserRole.ADMIN
    ):
        return {}

    if elevate_permissions:
        LOGGER.warning(
            "Permissions check with elevated permissions, likely due to access token usage"
        )
        return {}

    null_perm = {
        "$or": [
            {"creator_ids": {"$size": 0}},
            {"creator_ids": {"$in": [PUBLIC_USER_ID]}},
            {"creator_ids": {"$exists": False}},
        ]
    }
    if current_user.is_authenticated and current_user.person is not None:
        # find managed users under the given user (can later be expanded to groups)
        managed_users = list(
            get_database().users.find(
                {"managers": {"$in": [current_user.person.immutable_id]}}, projection={"_id": 1}
            )
        )
        if managed_users:
            managed_users = [u["_id"] for u in managed_users]
            LOGGER.debug("Found managed users %s for user %s", managed_users, current_user.person)

        # Create user permissions conditions related to their ownership of items and managed users
        user_perm_conditions = [
            {"creator_ids": {"$in": [current_user.person.immutable_id] + managed_users}}
        ]

        # If we are not restricting to user-only (i.e., writes, deletes), then also add group-based permissions
        if not user_only:
            user_group_ids = []
            if current_user.person.groups:
                user_group_ids = [group.immutable_id for group in current_user.person.groups]

            if user_group_ids:
                group_perm_conditions = {"group_ids": {"$in": user_group_ids}}
                user_perm_conditions.append(group_perm_conditions)

        user_perm: dict[str, Any] = {"$or": user_perm_conditions}

        if user_only:
            # TODO: remove this hack when permissions are refactored. Currently starting_materials and equipment
            # are a special case that should be group editable, so even when the route has asked to only edit this
            # user's stuff, we can also let starting materials and equipment through.

            # If we are trying to delete, then make sure they cannot delete items that do not match their user
            if deleting:
                return user_perm

            user_perm = {"$or": [user_perm, {"type": {"$in": ["starting_materials", "equipment"]}}]}
            return user_perm

        return {"$or": [user_perm, null_perm]}

    elif user_only:
        return {"_id": -1}

    return null_perm
