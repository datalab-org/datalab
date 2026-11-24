"""Single-use tool launch grants and delegated tool sessions."""

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha512
from typing import Literal

from bson import ObjectId
from bson.errors import InvalidId
from flask import current_app, has_app_context
from pymongo import ReturnDocument

from pydatalab.login import AuthMethod, get_by_id
from pydatalab.models.people import AccountStatus
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import Key

from .base import ItemSelection, ToolContext, ToolLaunchGrantIssuer, ToolSessionPolicy

DEFAULT_LAUNCH_LIFETIME_SECONDS = 60
DEFAULT_TOOL_SESSION_LIFETIME_SECONDS = 24 * 60 * 60
MAX_LAUNCH_LIFETIME_SECONDS = 10 * 60
MAX_TOOL_SESSION_LIFETIME_SECONDS = DEFAULT_TOOL_SESSION_LIFETIME_SECONDS
MAX_RENEWABLE_TOOL_SESSION_AGE_SECONDS = 7 * 24 * 60 * 60
TOOL_SELECTION_LIFETIME_SECONDS = 10 * 60
_TOOL_LAUNCH_PURPOSE = "tool-launch"
_TOOL_SELECTION_PURPOSE = "tool-selection"
_TOOL_SESSION_ID_DOMAIN = b"datalab:delegated-tool-session:v1\0"
_MAX_CANDIDATE_TOOL_ACCESS_TOKEN_LENGTH = 4096


class _DelegatedToolAccessToken(Key):
    """Stored credentials for one delegated tool session."""

    tool_id: str
    client_id: str
    hash: str
    type: Literal["tool_access_token"] = "tool_access_token"


def _hash_secret(value: str) -> str:
    return sha512(value.encode("utf-8")).hexdigest()


def _delegated_tool_session_id(user_id: ObjectId, tool_id: str) -> str:
    """Return the canonical document ID for one user's provider session."""
    digest = sha512(_TOOL_SESSION_ID_DOMAIN)
    digest.update(user_id.binary)
    digest.update(b"\0")
    digest.update(tool_id.encode("utf-8"))
    return digest.hexdigest()


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass(frozen=True)
class DelegatedToolSession:
    """Tool access token returned once for a delegated tool session."""

    tool_access_token: str
    expires_at: datetime


@dataclass(frozen=True)
class ToolLaunchExchange:
    """Tool context and delegated tool session produced by a launch code exchange."""

    context: ToolContext
    tool_session: DelegatedToolSession
    selection: ItemSelection | None
    session_reused: bool = False
    session_renewed: bool = False


@dataclass(frozen=True)
class _ConsumedLaunchGrant:
    """Internal data recovered from one atomically consumed launch grant."""

    user_id: str
    selection: ItemSelection | None
    session_policy: ToolSessionPolicy
    allow_session_renewal: bool


@dataclass(frozen=True)
class _ReusableToolSession:
    """Validated canonical candidate and its stored comparison values."""

    session: DelegatedToolSession
    created_at: datetime
    stored_created_at: datetime
    stored_expires_at: datetime


@dataclass(frozen=True)
class BoundToolLaunchGrantIssuer(ToolLaunchGrantIssuer):
    """Tool launch grant capability bound to one provider and current user."""

    tool_id: str
    user_id: str
    selection: ItemSelection | None = None

    def issue(
        self,
        client_id: str,
        lifetime_seconds: int = DEFAULT_LAUNCH_LIFETIME_SECONDS,
        *,
        session_policy: ToolSessionPolicy = ToolSessionPolicy.REPLACE,
        allow_session_renewal: bool = False,
    ) -> str:
        """Create a hashed, expiring tool launch grant and return its raw code."""
        if not isinstance(client_id, str) or not client_id.strip():
            raise ValueError("Launch-grant client ID must not be empty")
        if type(lifetime_seconds) is not int or not (
            1 <= lifetime_seconds <= MAX_LAUNCH_LIFETIME_SECONDS
        ):
            raise ValueError(
                f"Tool launch grants must expire within {MAX_LAUNCH_LIFETIME_SECONDS} seconds"
            )
        if not isinstance(session_policy, ToolSessionPolicy):
            raise ValueError("Unsupported tool session policy")
        if type(allow_session_renewal) is not bool:
            raise ValueError("Session renewal permission must be a boolean")
        if allow_session_renewal and session_policy is not ToolSessionPolicy.REUSE_OR_REPLACE:
            raise ValueError("Session renewal requires the reuse-or-replace policy")

        created_at = _now()
        code = secrets.token_urlsafe(32)
        flask_mongo.db.tool_launch_grants.insert_one(
            {
                "_id": _hash_secret(code),
                "user_id": ObjectId(self.user_id),
                "tool_id": self.tool_id,
                "client_id": client_id,
                "purpose": _TOOL_LAUNCH_PURPOSE,
                "session_policy": session_policy.value,
                "allow_session_renewal": allow_session_renewal,
                "selection": self.selection.model_dump() if self.selection else None,
                "created_at": created_at,
                "expires_at": created_at + timedelta(seconds=lifetime_seconds),
            }
        )
        return code


def _consume_launch_code(
    code: str,
    tool_id: str,
    client_id: str,
    expected_user_id: str | None = None,
) -> _ConsumedLaunchGrant | None:
    """Atomically consume one matching, unexpired tool launch grant."""
    if not code or not tool_id or not client_id:
        return None

    query: dict[str, object] = {
        "_id": _hash_secret(code),
        "tool_id": tool_id,
        "client_id": client_id,
        "purpose": _TOOL_LAUNCH_PURPOSE,
        "expires_at": {"$gt": _now()},
    }
    if expected_user_id is not None:
        try:
            query["user_id"] = ObjectId(expected_user_id)
        except (InvalidId, TypeError):
            return None

    grant = flask_mongo.db.tool_launch_grants.find_one_and_delete(query)
    if grant is None:
        return None
    try:
        selection_data = grant.get("selection")
        selection = ItemSelection.model_validate(selection_data) if selection_data else None
        if "session_policy" not in grant:
            session_policy = ToolSessionPolicy.REPLACE
        else:
            stored_policy = grant["session_policy"]
            if not isinstance(stored_policy, str):
                return None
            session_policy = ToolSessionPolicy(stored_policy)
        if "allow_session_renewal" not in grant:
            allow_session_renewal = False
        else:
            allow_session_renewal = grant["allow_session_renewal"]
            if type(allow_session_renewal) is not bool:
                return None
        if allow_session_renewal and session_policy is not ToolSessionPolicy.REUSE_OR_REPLACE:
            return None
    except (TypeError, ValueError):
        return None
    return _ConsumedLaunchGrant(
        user_id=str(grant["user_id"]),
        selection=selection,
        session_policy=session_policy,
        allow_session_renewal=allow_session_renewal,
    )


def issue_tool_selection_code(
    *,
    user_id: str,
    tool_id: str,
    selection: ItemSelection,
) -> str:
    """Issue a short-lived code that hands a selection to its delegated tool."""
    created_at = _now()
    code = secrets.token_urlsafe(32)
    flask_mongo.db.tool_launch_grants.insert_one(
        {
            "_id": _hash_secret(code),
            "user_id": ObjectId(user_id),
            "tool_id": tool_id,
            "purpose": _TOOL_SELECTION_PURPOSE,
            "selection": selection.model_dump(),
            "created_at": created_at,
            "expires_at": created_at + timedelta(seconds=TOOL_SELECTION_LIFETIME_SECONDS),
        }
    )
    return code


def consume_tool_selection_code(
    *,
    code: str,
    tool_id: str,
    tool_access_token: str,
    expected_user_id: str,
) -> ItemSelection | None:
    """Consume one selection using an active token for the same user and tool."""
    if not code or not tool_access_token:
        return None
    try:
        user_id = ObjectId(expected_user_id)
    except (InvalidId, TypeError):
        return None

    session = flask_mongo.db.tool_sessions.find_one(
        {
            "hash": _hash_secret(tool_access_token),
            "user": user_id,
            "tool_id": tool_id,
            "type": "tool_access_token",
            "expires_at": {"$gt": _now()},
        },
        projection={"_id": 1},
    )
    if session is None:
        return None

    grant = flask_mongo.db.tool_launch_grants.find_one_and_delete(
        {
            "_id": _hash_secret(code),
            "user_id": user_id,
            "tool_id": tool_id,
            "purpose": _TOOL_SELECTION_PURPOSE,
            "expires_at": {"$gt": _now()},
        }
    )
    if grant is None:
        return None
    try:
        return ItemSelection.model_validate(grant["selection"])
    except (KeyError, TypeError, ValueError):
        return None


def create_delegated_tool_session(
    user_id: str,
    tool_id: str,
    client_id: str,
    lifetime_seconds: int = DEFAULT_TOOL_SESSION_LIFETIME_SECONDS,
) -> DelegatedToolSession:
    """Issue a tool access token for one delegated tool session."""
    if not 1 <= lifetime_seconds <= MAX_TOOL_SESSION_LIFETIME_SECONDS:
        raise ValueError(
            "Delegated tool sessions must expire within "
            f"{MAX_TOOL_SESSION_LIFETIME_SECONDS} seconds"
        )

    stored_user_id = ObjectId(user_id)
    session_id = _delegated_tool_session_id(stored_user_id, tool_id)
    created_at = _now()
    expires_at = created_at + timedelta(seconds=lifetime_seconds)
    tool_access_token = secrets.token_urlsafe(48)
    stored_token = _DelegatedToolAccessToken(
        user=stored_user_id,
        tool_id=tool_id,
        client_id=client_id,
        hash=_hash_secret(tool_access_token),
        created_at=created_at,
        expires_at=expires_at,
        version=1,
    )
    session_query = {
        "user": stored_user_id,
        "tool_id": tool_id,
        "type": "tool_access_token",
    }
    flask_mongo.db.tool_sessions.delete_many(
        {
            **session_query,
            "_id": {"$ne": session_id},
        }
    )
    flask_mongo.db.tool_sessions.replace_one(
        {"_id": session_id},
        {"_id": session_id, **stored_token.model_dump()},
        upsert=True,
    )
    return DelegatedToolSession(
        tool_access_token=tool_access_token,
        expires_at=expires_at,
    )


def _create_independent_delegated_tool_session(
    user_id: str,
    tool_id: str,
    client_id: str,
    lifetime_seconds: int,
) -> DelegatedToolSession:
    """Issue a delegated session without replacing another provider session."""
    stored_user_id = ObjectId(user_id)
    created_at = _now()
    expires_at = created_at + timedelta(seconds=lifetime_seconds)
    tool_access_token = secrets.token_urlsafe(48)
    stored_token = _DelegatedToolAccessToken(
        user=stored_user_id,
        tool_id=tool_id,
        client_id=client_id,
        hash=_hash_secret(tool_access_token),
        created_at=created_at,
        expires_at=expires_at,
        version=1,
    )
    flask_mongo.db.tool_sessions.insert_one(stored_token.model_dump())
    return DelegatedToolSession(
        tool_access_token=tool_access_token,
        expires_at=expires_at,
    )


def _bson_utc_now() -> datetime:
    """Return the current UTC time at MongoDB's millisecond precision."""
    now = _now().astimezone(timezone.utc)
    return now.replace(microsecond=(now.microsecond // 1000) * 1000)


def _normalise_stored_datetime(value: object) -> datetime | None:
    """Normalise a MongoDB datetime, treating a naive value as UTC."""
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _find_reusable_tool_session(
    user_id: str,
    tool_id: str,
    client_id: str,
    candidate_tool_access_token: str,
    lifetime_seconds: int,
    decision_time: datetime,
    minimum_reuse_lifetime_seconds: int | None,
) -> _ReusableToolSession | None:
    """Load and validate an exact canonical candidate at one decision time."""
    stored_user_id = ObjectId(user_id)
    session_id = _delegated_tool_session_id(stored_user_id, tool_id)
    stored = flask_mongo.db.tool_sessions.find_one(
        {
            "_id": session_id,
            "user": stored_user_id,
            "tool_id": tool_id,
            "client_id": client_id,
            "hash": _hash_secret(candidate_tool_access_token),
            "type": "tool_access_token",
            "version": 1,
            "expires_at": {"$gt": decision_time},
        }
    )
    if stored is None:
        return None

    created_at = _normalise_stored_datetime(stored.get("created_at"))
    expires_at = _normalise_stored_datetime(stored.get("expires_at"))
    absolute_end = (
        created_at + timedelta(seconds=MAX_RENEWABLE_TOOL_SESSION_AGE_SECONDS)
        if created_at is not None
        else None
    )
    if (
        created_at is None
        or expires_at is None
        or created_at > decision_time
        or expires_at <= created_at
        or expires_at <= decision_time
        or absolute_end is None
        or decision_time >= absolute_end
        or expires_at > absolute_end
        or expires_at > decision_time + timedelta(seconds=lifetime_seconds)
        or (
            minimum_reuse_lifetime_seconds is not None
            and expires_at < decision_time + timedelta(seconds=minimum_reuse_lifetime_seconds)
        )
    ):
        return None

    sibling = flask_mongo.db.tool_sessions.find_one(
        {
            "_id": {"$ne": session_id},
            "user": stored_user_id,
            "tool_id": tool_id,
            "type": "tool_access_token",
            "expires_at": {"$gt": decision_time},
        },
        projection={"_id": 1},
    )
    if sibling is not None:
        return None

    return _ReusableToolSession(
        session=DelegatedToolSession(
            tool_access_token=candidate_tool_access_token,
            expires_at=expires_at,
        ),
        created_at=created_at,
        stored_created_at=stored["created_at"],
        stored_expires_at=stored["expires_at"],
    )


def _reuse_delegated_tool_session(
    user_id: str,
    tool_id: str,
    client_id: str,
    candidate_tool_access_token: str | None,
    lifetime_seconds: int,
    minimum_reuse_lifetime_seconds: int,
) -> DelegatedToolSession | None:
    """Return an eligible exact canonical candidate without changing storage."""
    if candidate_tool_access_token is None:
        return None
    candidate = _find_reusable_tool_session(
        user_id=user_id,
        tool_id=tool_id,
        client_id=client_id,
        candidate_tool_access_token=candidate_tool_access_token,
        lifetime_seconds=lifetime_seconds,
        decision_time=_bson_utc_now(),
        minimum_reuse_lifetime_seconds=minimum_reuse_lifetime_seconds,
    )
    return candidate.session if candidate is not None else None


def _renew_delegated_tool_session(
    user_id: str,
    tool_id: str,
    client_id: str,
    candidate_tool_access_token: str | None,
    lifetime_seconds: int,
    minimum_reuse_lifetime_seconds: int,
) -> tuple[DelegatedToolSession | None, bool]:
    """Renew an eligible canonical candidate using one exact compare-and-set."""
    if candidate_tool_access_token is None:
        return None, False

    decision_time = _bson_utc_now()
    candidate = _find_reusable_tool_session(
        user_id=user_id,
        tool_id=tool_id,
        client_id=client_id,
        candidate_tool_access_token=candidate_tool_access_token,
        lifetime_seconds=lifetime_seconds,
        decision_time=decision_time,
        minimum_reuse_lifetime_seconds=None,
    )
    if candidate is None:
        return None, False

    requested_end = decision_time + timedelta(seconds=lifetime_seconds)
    absolute_end = candidate.created_at + timedelta(seconds=MAX_RENEWABLE_TOOL_SESSION_AGE_SECONDS)
    renewal_end = min(requested_end, absolute_end)
    minimum_end = decision_time + timedelta(seconds=minimum_reuse_lifetime_seconds)
    if renewal_end < minimum_end:
        return None, False
    if renewal_end <= candidate.session.expires_at:
        # An explicit renewal at the absolute age cap must rotate instead of
        # returning a credential whose expiry was not extended.
        if renewal_end == absolute_end:
            return None, False
        if candidate.session.expires_at >= minimum_end:
            return candidate.session, False
        return None, False

    stored_user_id = ObjectId(user_id)
    session_id = _delegated_tool_session_id(stored_user_id, tool_id)
    updated = flask_mongo.db.tool_sessions.find_one_and_update(
        {
            "_id": session_id,
            "user": stored_user_id,
            "tool_id": tool_id,
            "client_id": client_id,
            "hash": _hash_secret(candidate_tool_access_token),
            "type": "tool_access_token",
            "version": 1,
            "created_at": candidate.stored_created_at,
            "$and": [
                {"expires_at": candidate.stored_expires_at},
                {"expires_at": {"$gt": decision_time}},
            ],
        },
        {"$set": {"expires_at": renewal_end}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is not None:
        expires_at = _normalise_stored_datetime(updated.get("expires_at"))
        if expires_at is not None:
            return DelegatedToolSession(candidate_tool_access_token, expires_at), True
        return None, False

    final_candidate = _find_reusable_tool_session(
        user_id=user_id,
        tool_id=tool_id,
        client_id=client_id,
        candidate_tool_access_token=candidate_tool_access_token,
        lifetime_seconds=lifetime_seconds,
        decision_time=decision_time,
        minimum_reuse_lifetime_seconds=minimum_reuse_lifetime_seconds,
    )
    if (
        final_candidate is not None
        and final_candidate.session.expires_at > candidate.session.expires_at
        and final_candidate.session.expires_at <= renewal_end
    ):
        return final_candidate.session, False
    return None, False


def get_tool_access_token_user_id(tool_access_token: str) -> str | None:
    """Return the user bound to an unexpired tool access token."""
    session = flask_mongo.db.tool_sessions.find_one(
        {
            "hash": _hash_secret(tool_access_token),
            "type": "tool_access_token",
            "expires_at": {"$gt": _now()},
        },
        projection={"user": 1, "tool_id": 1},
    )
    if session is None:
        return None
    tool_id = session.get("tool_id")
    if not isinstance(tool_id, str) or not has_app_context():
        return None

    from .registry import TOOL_REGISTRY_EXTENSION, ToolRegistry

    registry = current_app.extensions.get(TOOL_REGISTRY_EXTENSION)
    if not isinstance(registry, ToolRegistry) or not registry.is_enabled(tool_id):
        return None
    return str(session["user"])


def _exchange_launch_code(
    code: str,
    tool_id: str,
    client_id: str,
    tool_session_lifetime_seconds: int = DEFAULT_TOOL_SESSION_LIFETIME_SECONDS,
    *,
    expected_user_id: str | None,
    candidate_tool_access_token: str | None,
    minimum_reuse_lifetime_seconds: int,
    renew_existing_session: bool,
) -> ToolLaunchExchange | None:
    """Implement bound and service launch-code exchanges."""
    if type(tool_session_lifetime_seconds) is not int or not (
        1 <= tool_session_lifetime_seconds <= MAX_TOOL_SESSION_LIFETIME_SECONDS
    ):
        raise ValueError(
            "Delegated tool sessions must expire within "
            f"{MAX_TOOL_SESSION_LIFETIME_SECONDS} seconds"
        )
    if type(minimum_reuse_lifetime_seconds) is not int or not (
        0 <= minimum_reuse_lifetime_seconds <= tool_session_lifetime_seconds
    ):
        raise ValueError(
            "Minimum reuse lifetime must be between zero and the delegated session lifetime"
        )
    if candidate_tool_access_token is not None and (
        not isinstance(candidate_tool_access_token, str)
        or len(candidate_tool_access_token) > _MAX_CANDIDATE_TOOL_ACCESS_TOKEN_LENGTH
    ):
        raise ValueError("Candidate tool access token is invalid")
    if type(renew_existing_session) is not bool:
        raise ValueError("Session renewal request must be a boolean")

    grant = _consume_launch_code(
        code,
        tool_id,
        client_id,
        expected_user_id=expected_user_id,
    )
    if grant is None:
        return None
    if renew_existing_session and not grant.allow_session_renewal:
        return None

    # Resolve the delegated identity so the exchange context reports the same effective
    # role as the tool access token issued below.
    user = get_by_id(
        grant.user_id,
        auth_method=AuthMethod.TOOL_ACCESS_TOKEN,
    )
    if user is None or user.account_status != AccountStatus.ACTIVE:
        return None

    groups = user.groups or []
    context = ToolContext(
        user_id=grant.user_id,
        display_name=user.display_name,
        role=user.role.value,
        group_ids=tuple(str(group.immutable_id) for group in groups),
    )
    session_reused = False
    session_renewed = False
    if grant.session_policy is ToolSessionPolicy.REUSE_OR_REPLACE:
        if renew_existing_session:
            tool_session, session_renewed = _renew_delegated_tool_session(
                user_id=grant.user_id,
                tool_id=tool_id,
                client_id=client_id,
                candidate_tool_access_token=candidate_tool_access_token,
                lifetime_seconds=tool_session_lifetime_seconds,
                minimum_reuse_lifetime_seconds=minimum_reuse_lifetime_seconds,
            )
        else:
            tool_session = _reuse_delegated_tool_session(
                user_id=grant.user_id,
                tool_id=tool_id,
                client_id=client_id,
                candidate_tool_access_token=candidate_tool_access_token,
                lifetime_seconds=tool_session_lifetime_seconds,
                minimum_reuse_lifetime_seconds=minimum_reuse_lifetime_seconds,
            )
        session_reused = tool_session is not None
        if tool_session is None:
            tool_session = create_delegated_tool_session(
                user_id=grant.user_id,
                tool_id=tool_id,
                client_id=client_id,
                lifetime_seconds=tool_session_lifetime_seconds,
            )
    elif grant.session_policy is ToolSessionPolicy.INDEPENDENT:
        tool_session = _create_independent_delegated_tool_session(
            user_id=grant.user_id,
            tool_id=tool_id,
            client_id=client_id,
            lifetime_seconds=tool_session_lifetime_seconds,
        )
    else:
        tool_session = create_delegated_tool_session(
            user_id=grant.user_id,
            tool_id=tool_id,
            client_id=client_id,
            lifetime_seconds=tool_session_lifetime_seconds,
        )
    return ToolLaunchExchange(
        context=context,
        tool_session=tool_session,
        selection=grant.selection,
        session_reused=session_reused,
        session_renewed=session_renewed,
    )


def exchange_launch_code(
    code: str,
    tool_id: str,
    client_id: str,
    tool_session_lifetime_seconds: int = DEFAULT_TOOL_SESSION_LIFETIME_SECONDS,
    *,
    expected_user_id: str,
    candidate_tool_access_token: str | None = None,
    minimum_reuse_lifetime_seconds: int = 0,
    renew_existing_session: bool = False,
) -> ToolLaunchExchange | None:
    """Exchange a launch code bound to the authenticated browser user.

    A candidate is considered only for a grant bound to ``REUSE_OR_REPLACE``
    and must retain at least ``minimum_reuse_lifetime_seconds``. Any reuse miss
    follows that policy's replacement path. Renewal additionally requires
    grant-bound permission and an explicit ``renew_existing_session`` request.
    """
    if not isinstance(expected_user_id, str) or not expected_user_id.strip():
        raise ValueError("Expected user ID must not be empty")
    return _exchange_launch_code(
        code,
        tool_id,
        client_id,
        tool_session_lifetime_seconds,
        expected_user_id=expected_user_id,
        candidate_tool_access_token=candidate_tool_access_token,
        minimum_reuse_lifetime_seconds=minimum_reuse_lifetime_seconds,
        renew_existing_session=renew_existing_session,
    )


def exchange_service_launch_code(
    code: str,
    tool_id: str,
    client_id: str,
    tool_session_lifetime_seconds: int = DEFAULT_TOOL_SESSION_LIFETIME_SECONDS,
    *,
    candidate_tool_access_token: str | None = None,
    minimum_reuse_lifetime_seconds: int = 0,
    renew_existing_session: bool = False,
) -> ToolLaunchExchange | None:
    """Exchange a launch code without browser-user binding.

    This function does not authenticate its caller. It may only be called after
    a confidential service client has been authenticated.

    A candidate is considered only for a grant bound to ``REUSE_OR_REPLACE``
    and must retain at least ``minimum_reuse_lifetime_seconds``. Any reuse miss
    follows that policy's replacement path. Renewal additionally requires
    grant-bound permission and an explicit ``renew_existing_session`` request.
    """
    return _exchange_launch_code(
        code,
        tool_id,
        client_id,
        tool_session_lifetime_seconds,
        expected_user_id=None,
        candidate_tool_access_token=candidate_tool_access_token,
        minimum_reuse_lifetime_seconds=minimum_reuse_lifetime_seconds,
        renew_existing_session=renew_existing_session,
    )
