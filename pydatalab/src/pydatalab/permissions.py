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


def _get_base_permissions(
    user_only: bool = True, deleting: bool = False, elevate_permissions: bool = False
) -> dict[str, Any]:
    """Build the MongoDB permission filter without collection-inheritance —
    i.e., based purely on `creator_ids`/`group_ids` and the various admin/
    testing/access-token short-circuits.
    """
    if CONFIG.TESTING:
        return {}

    # Super-user mode for admins: only activates on GET with ?sudo=1
    # For non-GET methods, admins always have full access
    if (
        current_user.is_authenticated
        and current_user.person is not None
        and current_user.account_status == AccountStatus.ACTIVE
        and current_user.role == UserRole.ADMIN
    ):
        # Non-GET methods: admin always has full access
        if request.method != "GET":
            return {}
        # GET methods: require ?sudo=1 for full access
        if request.args.get("sudo") == "1":
            return {}
        # Otherwise: treat admin as normal user (fall through)

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

    # Define permission for inventory items with no groups (accessible to all)
    null_group_perm = {
        "$or": [
            {"group_ids": {"$size": 0}},
            {"group_ids": {"$exists": False}},
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
            if deleting:
                return user_perm
            else:
                inventory_types_perm = {
                    "$and": [
                        {"type": {"$in": ["starting_materials", "equipment"]}},
                        null_group_perm,
                    ]
                }
                return {"$or": [user_perm, inventory_types_perm]}
        else:
            inventory_types_perm = {
                "$and": [{"type": {"$in": ["starting_materials", "equipment"]}}, null_group_perm]
            }
            return {"$or": [user_perm, null_perm, inventory_types_perm]}

    elif user_only:
        return {"_id": -1}

    return null_perm


def get_default_permissions(
    user_only: bool = True,
    deleting: bool = False,
    elevate_permissions: bool = False,
    inherit_from_collections: bool = True,
) -> dict[str, Any]:
    """Return the MongoDB query terms corresponding to the current user.

    Will return open permissions if a) the `CONFIG.TESTING` parameter is `True`,
    or b) if the current user is registered as an admin and has opted into super-user
    mode via `?sudo=1` (for GET requests) or is performing a write operation.

    For read paths (`user_only=False`), the filter is by default widened to
    include any document whose `relationships` link it to a collection the
    current user can read — i.e., items inherit read access from collections
    they are members of. Write paths (`user_only=True`) never inherit;
    collection membership grants read but not edit/delete on member items.

    Parameters:
        user_only: Whether to exclude items that also have no attached user (`False`),
            i.e., public items. This should be set to `False` when reading (and wanting
            to return public items), but left as `True` when modifying or removing items.
        elevate_permissions: Whether to elevate this query's permissions, i.e., in the case
            that an item-specific access token has been provided elsewhere.
        inherit_from_collections: Whether read access should be inherited from
            collections the user can read. Set this to `False` for endpoints
            that should only show items the user directly owns or is a member
            of (e.g., a "My samples" listing) — the user can still discover
            collection-shared items by navigating into the collection. Has
            no effect when `user_only=True`.

    """
    base = _get_base_permissions(
        user_only=user_only, deleting=deleting, elevate_permissions=elevate_permissions
    )
    # Inheritance is read-only, and unnecessary when the base already
    # short-circuits to a fully-open or fully-closed filter.
    if user_only or not inherit_from_collections or base == {} or base == {"_id": -1}:
        return base

    collection_ids = [
        doc["_id"]
        for doc in flask_mongo.db.collections.find(
            _get_base_permissions(user_only=False), {"_id": 1}
        )
    ]
    if not collection_ids:
        return base

    inheritance = {
        "relationships": {
            "$elemMatch": {"type": "collections", "immutable_id": {"$in": collection_ids}}
        }
    }

    if "$or" in base and len(base) == 1:
        return {"$or": [*base["$or"], inheritance]}
    return {"$or": [base, inheritance]}
