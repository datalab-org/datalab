from typing import Any, Dict

from flask_login import current_user

from pydatalab.config import CONFIG


def get_default_permissions(user_only: bool = True) -> Dict[str, Any]:
    """Return the MongoDB query terms corresponding to the current user.

    Parameters:
        user_only: Whether to exclude items that also have no attached user (`False`),
            i.e., public items. This should be set to `False` when reading (and wanting
            to return public items), but left as `True` when modifying or removing items.

    """

    if CONFIG.TESTING:
        return {}

    null_perm = {"creator_ids": {"$size": 0}}
    if current_user.is_authenticated and current_user.person is not None:
        user_perm = {"creator_ids": {"$in": [current_user.person.immutable_id]}}
        if user_only:
            return user_perm
        return {"$or": [user_perm, null_perm]}

    elif user_only:
        return {"_id": -1}

    return null_perm
