from functools import wraps
from typing import Any

from bson import ObjectId
from flask import request
from flask_login import current_user

from pydatalab.config import CONFIG
from pydatalab.login import UserRole
from pydatalab.models.people import AccountStatus
from pydatalab.mongo import get_database

PUBLIC_USER_ID = ObjectId(24 * "0")


def active_users_or_get_only(func):
    """Decorator to ensure that only active user accounts can access the route,
    unless it is a GET-route, in which case deactivated accounts can also access it.

    """

    @wraps(func)
    def wrapped_route(*args, **kwargs):
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


def get_default_permissions(user_only: bool = True, deleting: bool = False) -> dict[str, Any]:
    """Return the MongoDB query terms corresponding to the current user.

    Will return open permissions if a) the `CONFIG.TESTING` parameter is `True`,
    or b) if the current user is registered as an admin.

    Parameters:
        user_only: Whether to exclude items that also have no attached user (`False`),
            i.e., public items. This should be set to `False` when reading (and wanting
            to return public items), but left as `True` when modifying or removing items.

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

    null_perm = {
        "$or": [
            {"creator_ids": {"$size": 0}},
            {"creator_ids": {"$in": [PUBLIC_USER_ID]}},
            {"creator_ids": {"$exists": False}},
        ]
    }
    if current_user.is_authenticated and current_user.person is not None:
        managed_users = list(
            get_database().users.find(
                {"managers": {"$in": [current_user.person.immutable_id]}}, projection={"_id": 1}
            )
        )
        if managed_users:
            managed_users = [u["_id"] for u in managed_users]

        group_users = []
        if current_user.person.groups:
            user_group_ids = [group.immutable_id for group in current_user.person.groups]

            users_in_same_groups = list(
                get_database().users.find({"group_ids": {"$in": user_group_ids}}, {"_id": 1})
            )
            group_users_from_members = [u["_id"] for u in users_in_same_groups]

            groups_where_admin = list(
                get_database().groups.find(
                    {"group_admins": {"$in": [str(current_user.person.immutable_id)]}},
                    {"_id": 1, "group_admins": 1},
                )
            )

            group_users_from_admin = []
            if groups_where_admin:
                admin_group_ids = [g["_id"] for g in groups_where_admin]

                members_of_admin_groups = list(
                    get_database().users.find({"group_ids": {"$in": admin_group_ids}}, {"_id": 1})
                )
                group_users_from_admin = [u["_id"] for u in members_of_admin_groups]

                all_admins_from_groups = []
                for group in groups_where_admin:
                    all_admins_from_groups.extend(group.get("group_admins", []))

                admin_object_ids = [
                    ObjectId(admin_id) if isinstance(admin_id, str) else admin_id
                    for admin_id in all_admins_from_groups
                ]
                group_users_from_admin.extend(admin_object_ids)

            group_users = list(set(group_users_from_members + group_users_from_admin))

        user_perm: dict[str, Any] = {
            "creator_ids": {"$in": [current_user.person.immutable_id] + managed_users + group_users}
        }
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
