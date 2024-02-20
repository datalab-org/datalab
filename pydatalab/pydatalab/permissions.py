from typing import Any, Dict

from flask_login import current_user
from bson import ObjectId

from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER
from pydatalab.login import UserRole
from pydatalab.mongo import get_database


def get_default_permissions(user_only: bool = True) -> Dict[str, Any]:
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
        and current_user.role == UserRole.ADMIN
    ):
        return {}

    null_perm = {
        "$or": 
            [
                {"creator_ids": {"$size": 0}}, 
                {"creator_ids": {"$exists": False}}, 
                {"creator_ids": {"$in": [24*"0"]}},
                {"creator_ids": {"$in": [ObjectId(24*"0")]}},
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

        user_perm = {"creator_ids": {"$in": [current_user.person.immutable_id] + managed_users}}
        if user_only:
            return user_perm
        return {"$or": [user_perm, null_perm]}

    elif user_only:
        return {"_id": -1}

    return null_perm
