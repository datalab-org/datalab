from datetime import datetime, timedelta, timezone

import pytest
from flask.testing import FlaskClient

from pydatalab.config import CONFIG
from pydatalab.login import AuthMethod, get_by_api_key
from pydatalab.models.utils import UserRole
from pydatalab.mongo import create_default_indices
from pydatalab.permissions import get_default_permissions
from pydatalab.tools import (
    ItemSelection,
    ItemTableSelectionAction,
    StandaloneToolUI,
    ToolContext,
    ToolMetadata,
    ToolProvider,
    ToolSessionPolicy,
)
from pydatalab.tools import grants as tool_grants
from pydatalab.tools.grants import (
    BoundToolLaunchGrantIssuer,
    create_delegated_tool_session,
    exchange_launch_code,
    exchange_service_launch_code,
    get_tool_access_token_user_id,
    issue_tool_selection_code,
)
from pydatalab.tools.registry import TOOL_REGISTRY_EXTENSION, ToolRegistry


class ExampleTool(ToolProvider):
    id = "example-tool"
    metadata = ToolMetadata(
        name="Example tool",
        description="A test tool.",
        ui=StandaloneToolUI(),
        launch_actions=(
            ItemTableSelectionAction(
                id="compare-items",
                label="Compare items",
                tables=("samples",),
                min_items=2,
                max_items=3,
            ),
        ),
    )

    def launch(self, context, grants):
        code = grants.issue("example-client")
        return f"https://tools.example.test/start?code={code}"


class OtherExampleTool(ExampleTool):
    id = "other-example-tool"
    metadata = ToolMetadata(
        name="Other example tool",
        description="Another test tool.",
        ui=StandaloneToolUI(),
    )


@pytest.fixture
def tool_registry(app):
    previous = app.extensions[TOOL_REGISTRY_EXTENSION]
    registry = ToolRegistry()
    registry.register(ExampleTool())
    app.extensions[TOOL_REGISTRY_EXTENSION] = registry
    yield registry
    app.extensions[TOOL_REGISTRY_EXTENSION] = previous


@pytest.fixture(autouse=True)
def clean_tool_credentials(database):
    database.tool_launch_grants.delete_many({})
    database.tool_sessions.delete_many({})
    yield
    database.tool_launch_grants.delete_many({})
    database.tool_sessions.delete_many({})


def test_registry_rejects_duplicates_and_honours_disabled_tools(tool_registry, monkeypatch):
    context = ToolContext(user_id="user", display_name="User", role="user", group_ids=())

    assert tool_registry.available_for(context) == [tool_registry.get("example-tool")]

    monkeypatch.setattr(CONFIG.TOOLS, "DISABLED", {"example-tool"})
    assert tool_registry.available_for(context) == []

    with pytest.raises(ValueError, match="Duplicate tool provider"):
        tool_registry.register(ExampleTool())


def test_delegated_tool_token_uses_key_fields_and_is_isolated(
    app, database, tool_registry, user_id
):
    with app.app_context():
        session = create_delegated_tool_session(str(user_id), "example-tool", "example-client")
        stored = database.tool_sessions.find_one({"tool_id": "example-tool"})

        assert stored["user"] == user_id
        assert stored["client_id"] == "example-client"
        assert stored["type"] == "tool_access_token"
        assert stored["hash"] != session.tool_access_token
        assert database.api_keys.find_one({"type": "tool_access_token"}) is None
        assert get_tool_access_token_user_id(session.tool_access_token) == str(user_id)

        database.tool_sessions.update_one(
            {"_id": stored["_id"]},
            {"$set": {"expires_at": datetime.now(tz=timezone.utc) - timedelta(seconds=1)}},
        )
        assert get_tool_access_token_user_id(session.tool_access_token) is None


def test_delegated_tool_session_relaunch_replaces_only_same_user_and_provider(
    app,
    database,
    tool_registry,
    user_id,
    another_user_id,
):
    tool_registry.register(OtherExampleTool())

    with app.app_context():
        first = create_delegated_tool_session(str(user_id), "example-tool", "first-client")
        other_user = create_delegated_tool_session(
            str(another_user_id), "example-tool", "first-client"
        )
        other_tool = create_delegated_tool_session(
            str(user_id), "other-example-tool", "first-client"
        )
        replacement = create_delegated_tool_session(
            str(user_id), "example-tool", "replacement-client"
        )

        assert get_tool_access_token_user_id(first.tool_access_token) is None
        assert get_tool_access_token_user_id(replacement.tool_access_token) == str(user_id)
        assert get_tool_access_token_user_id(other_user.tool_access_token) == str(another_user_id)
        assert get_tool_access_token_user_id(other_tool.tool_access_token) == str(user_id)
        assert database.tool_sessions.count_documents({}) == 3
        stored = database.tool_sessions.find_one({"user": user_id, "tool_id": "example-tool"})
        assert stored["client_id"] == "replacement-client"


def test_tool_session_indexes(real_mongo_client):
    create_default_indices(real_mongo_client)
    indexes = real_mongo_client.get_database().tool_sessions.index_information()

    hash_index = indexes["unique delegated tool session hash"]
    assert hash_index["key"] == [("hash", 1)]
    assert hash_index["unique"] is True
    assert indexes["delegated tool session owner and provider"]["key"] == [
        ("user", 1),
        ("tool_id", 1),
        ("type", 1),
    ]
    assert set(indexes) == {
        "_id_",
        "expire delegated tool sessions",
        "unique delegated tool session hash",
        "delegated tool session owner and provider",
    }


def test_launch_grant_defaults_and_legacy_grants_replace_sessions(
    app, database, tool_registry, user_id
):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        first = create_delegated_tool_session(str(user_id), "example-tool", "old-client")

        default_code = issuer.issue("example-client", 60)
        stored_grant = database.tool_launch_grants.find_one({})
        assert stored_grant["session_policy"] == ToolSessionPolicy.REPLACE.value
        default_exchange = exchange_launch_code(
            default_code,
            "example-tool",
            "example-client",
            expected_user_id=str(user_id),
        )

        legacy_code = issuer.issue("example-client")
        database.tool_launch_grants.update_one(
            {},
            {"$unset": {"session_policy": ""}},
        )
        legacy_exchange = exchange_launch_code(
            legacy_code,
            "example-tool",
            "example-client",
            expected_user_id=str(user_id),
        )

        assert default_exchange is not None
        assert legacy_exchange is not None
        assert default_exchange.session_reused is False
        assert legacy_exchange.session_reused is False
        assert get_tool_access_token_user_id(first.tool_access_token) is None
        assert (
            get_tool_access_token_user_id(default_exchange.tool_session.tool_access_token) is None
        )
        assert get_tool_access_token_user_id(legacy_exchange.tool_session.tool_access_token) == str(
            user_id
        )


def test_launch_policy_and_reuse_arguments_are_strict_and_validated_before_consumption(
    app, database, tool_registry, user_id
):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        with pytest.raises(ValueError, match="Unsupported tool session policy"):
            issuer.issue("example-client", session_policy="independent")

        code = issuer.issue(
            "example-client",
            session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
        )
        for lifetime in (True, 1.5):
            with pytest.raises(ValueError, match="Delegated tool sessions"):
                exchange_launch_code(
                    code,
                    "example-tool",
                    "example-client",
                    lifetime,
                    expected_user_id=str(user_id),
                )
        for minimum in (-1, True, 24 * 60 * 60 + 1):
            with pytest.raises(ValueError, match="Minimum reuse lifetime"):
                exchange_launch_code(
                    code,
                    "example-tool",
                    "example-client",
                    expected_user_id=str(user_id),
                    minimum_reuse_lifetime_seconds=minimum,
                )
        with pytest.raises(ValueError, match="Candidate tool access token"):
            exchange_launch_code(
                code,
                "example-tool",
                "example-client",
                expected_user_id=str(user_id),
                candidate_tool_access_token="x" * 4097,
            )
        with pytest.raises(ValueError, match="Candidate tool access token"):
            exchange_launch_code(
                code,
                "example-tool",
                "example-client",
                expected_user_id=str(user_id),
                candidate_tool_access_token=object(),
            )

        exchange = exchange_launch_code(
            code,
            "example-tool",
            "example-client",
            expected_user_id=str(user_id),
        )
        assert exchange is not None

        malformed_code = issuer.issue("example-client")
        database.tool_launch_grants.update_one(
            {},
            {"$set": {"session_policy": None}},
        )
        assert (
            exchange_launch_code(
                malformed_code,
                "example-tool",
                "example-client",
                expected_user_id=str(user_id),
            )
            is None
        )

        unknown_code = issuer.issue("example-client")
        database.tool_launch_grants.update_one(
            {},
            {"$set": {"session_policy": "unknown"}},
        )
        assert (
            exchange_launch_code(
                unknown_code,
                "example-tool",
                "example-client",
                expected_user_id=str(user_id),
            )
            is None
        )
        assert (
            exchange_launch_code(
                malformed_code,
                "example-tool",
                "example-client",
                expected_user_id=str(user_id),
            )
            is None
        )


def test_exact_canonical_candidate_is_reused_without_database_mutation(
    app, database, tool_registry, user_id, monkeypatch
):
    fixed_now = datetime(2026, 1, 2, 3, 4, 5, 678000, tzinfo=timezone.utc)
    monkeypatch.setattr(tool_grants, "_now", lambda: fixed_now)

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        initial = exchange_launch_code(
            issuer.issue("example-client"),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
        )
        assert initial is not None
        stored_before = database.tool_sessions.find_one({})

        browser_reuse = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=initial.tool_session.tool_access_token,
            minimum_reuse_lifetime_seconds=200,
        )
        service_reuse = exchange_service_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            ),
            "example-tool",
            "example-client",
            300,
            candidate_tool_access_token=initial.tool_session.tool_access_token,
            minimum_reuse_lifetime_seconds=200,
        )

        assert browser_reuse is not None
        assert service_reuse is not None
        assert browser_reuse.session_reused is True
        assert service_reuse.session_reused is True
        assert (
            browser_reuse.tool_session.tool_access_token
            == service_reuse.tool_session.tool_access_token
            == initial.tool_session.tool_access_token
        )
        assert browser_reuse.tool_session.expires_at == initial.tool_session.expires_at
        assert database.tool_sessions.find_one({}) == stored_before


def test_launch_grant_renewal_permission_is_strict_and_policy_bound(
    app, database, tool_registry, user_id
):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        issuer.issue("example-client")
        stored_grant = database.tool_launch_grants.find_one({})
        assert stored_grant["allow_session_renewal"] is False

        for invalid_permission in (None, 0, 1, "true"):
            with pytest.raises(ValueError, match="renewal permission"):
                issuer.issue(
                    "example-client",
                    session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
                    allow_session_renewal=invalid_permission,
                )
        for policy in (ToolSessionPolicy.REPLACE, ToolSessionPolicy.INDEPENDENT):
            with pytest.raises(ValueError, match="reuse-or-replace"):
                issuer.issue(
                    "example-client",
                    session_policy=policy,
                    allow_session_renewal=True,
                )

        code = issuer.issue(
            "example-client",
            session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            allow_session_renewal=True,
        )
        stored_grant = database.tool_launch_grants.find_one({"_id": tool_grants._hash_secret(code)})
        assert stored_grant["allow_session_renewal"] is True


def test_renewal_request_is_validated_before_grant_consumption(
    app, database, tool_registry, user_id
):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        code = issuer.issue(
            "example-client",
            session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            allow_session_renewal=True,
        )

        with pytest.raises(ValueError, match="renewal request"):
            exchange_launch_code(
                code,
                "example-tool",
                "example-client",
                expected_user_id=str(user_id),
                renew_existing_session=1,
            )

        assert database.tool_launch_grants.count_documents({}) == 1
        exchange = exchange_launch_code(
            code,
            "example-tool",
            "example-client",
            expected_user_id=str(user_id),
        )
        assert exchange is not None


def test_unauthorized_renewal_consumes_grant_without_session_mutation(
    app, database, tool_registry, user_id
):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        candidate = create_delegated_tool_session(
            str(user_id), "example-tool", "example-client", 300
        )
        stored_before = database.tool_sessions.find_one({})
        code = issuer.issue(
            "example-client",
            session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
        )

        exchange = exchange_launch_code(
            code,
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=candidate.tool_access_token,
            renew_existing_session=True,
        )

        assert exchange is None
        assert database.tool_launch_grants.count_documents({}) == 0
        assert database.tool_sessions.find_one({}) == stored_before


@pytest.mark.parametrize("service_exchange", (False, True))
def test_renewal_preserves_the_candidate_and_advances_only_expiry(
    app, database, tool_registry, user_id, monkeypatch, service_exchange
):
    fixed_now = datetime(2026, 1, 2, 3, 4, 5, 678901, tzinfo=timezone.utc)
    decision_time = fixed_now.replace(microsecond=678000)
    monkeypatch.setattr(tool_grants, "_now", lambda: fixed_now)

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        candidate = create_delegated_tool_session(
            str(user_id), "example-tool", "example-client", 60
        )
        stored_before = database.tool_sessions.find_one({})
        code = issuer.issue(
            "example-client",
            session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            allow_session_renewal=True,
        )

        exchange_kwargs = {
            "candidate_tool_access_token": candidate.tool_access_token,
            "minimum_reuse_lifetime_seconds": 200,
            "renew_existing_session": True,
        }
        if service_exchange:
            exchange = exchange_service_launch_code(
                code, "example-tool", "example-client", 300, **exchange_kwargs
            )
        else:
            exchange = exchange_launch_code(
                code,
                "example-tool",
                "example-client",
                300,
                expected_user_id=str(user_id),
                **exchange_kwargs,
            )

        assert exchange is not None
        assert exchange.session_reused is True
        assert exchange.session_renewed is True
        assert exchange.tool_session.tool_access_token == candidate.tool_access_token
        assert exchange.tool_session.expires_at == decision_time + timedelta(seconds=300)
        stored_after = database.tool_sessions.find_one({})
        assert stored_after["expires_at"] == exchange.tool_session.expires_at.replace(tzinfo=None)
        assert {key: value for key, value in stored_after.items() if key != "expires_at"} == {
            key: value for key, value in stored_before.items() if key != "expires_at"
        }


def test_renewal_uses_the_absolute_age_cap_and_replaces_when_minimum_cannot_be_met(
    app, database, tool_registry, user_id, monkeypatch
):
    fixed_now = datetime(2026, 1, 8, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(tool_grants, "_now", lambda: fixed_now)

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        candidate = create_delegated_tool_session(
            str(user_id), "example-tool", "example-client", 60
        )
        capped_creation = fixed_now - timedelta(days=7) + timedelta(seconds=100)
        database.tool_sessions.update_one(
            {},
            {
                "$set": {
                    "created_at": capped_creation,
                    "expires_at": fixed_now + timedelta(seconds=20),
                }
            },
        )
        capped_exchange = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
                allow_session_renewal=True,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=candidate.tool_access_token,
            minimum_reuse_lifetime_seconds=100,
            renew_existing_session=True,
        )

        assert capped_exchange is not None
        assert capped_exchange.session_reused is True
        assert capped_exchange.session_renewed is True
        assert capped_exchange.tool_session.expires_at == capped_creation + timedelta(days=7)

        database.tool_sessions.update_one(
            {},
            {
                "$set": {
                    "created_at": fixed_now - timedelta(days=7) + timedelta(seconds=50),
                    "expires_at": fixed_now + timedelta(seconds=20),
                }
            },
        )
        replacement = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
                allow_session_renewal=True,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=candidate.tool_access_token,
            minimum_reuse_lifetime_seconds=60,
            renew_existing_session=True,
        )

        assert replacement is not None
        assert replacement.session_reused is False
        assert replacement.session_renewed is False
        assert replacement.tool_session.tool_access_token != candidate.tool_access_token


def test_renewal_replaces_candidate_already_at_absolute_age_cap(
    app, database, tool_registry, user_id, monkeypatch
):
    fixed_now = datetime(2026, 1, 8, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(tool_grants, "_now", lambda: fixed_now)

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        candidate = create_delegated_tool_session(
            str(user_id), "example-tool", "example-client", 3600
        )
        absolute_end = fixed_now + timedelta(minutes=30)
        database.tool_sessions.update_one(
            {},
            {
                "$set": {
                    "created_at": absolute_end - timedelta(days=7),
                    "expires_at": absolute_end,
                }
            },
        )

        exchange = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
                allow_session_renewal=True,
            ),
            "example-tool",
            "example-client",
            3600,
            expected_user_id=str(user_id),
            candidate_tool_access_token=candidate.tool_access_token,
            minimum_reuse_lifetime_seconds=10 * 60,
            renew_existing_session=True,
        )

        assert exchange is not None
        assert exchange.session_reused is False
        assert exchange.session_renewed is False
        assert exchange.tool_session.tool_access_token != candidate.tool_access_token
        assert get_tool_access_token_user_id(candidate.tool_access_token) is None


def test_repeated_renewal_uses_a_rolling_horizon_without_stacking(
    app, database, tool_registry, user_id, monkeypatch
):
    clock = [datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)]
    monkeypatch.setattr(tool_grants, "_now", lambda: clock[0])

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        candidate = create_delegated_tool_session(
            str(user_id), "example-tool", "example-client", 60
        )

        first = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
                allow_session_renewal=True,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=candidate.tool_access_token,
            renew_existing_session=True,
        )
        clock[0] += timedelta(seconds=30)
        second = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
                allow_session_renewal=True,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=candidate.tool_access_token,
            renew_existing_session=True,
        )

        assert first is not None
        assert second is not None
        assert first.tool_session.expires_at == clock[0] + timedelta(seconds=270)
        assert second.tool_session.expires_at == clock[0] + timedelta(seconds=300)
        assert second.tool_session.tool_access_token == candidate.tool_access_token
        assert second.session_renewed is True


def test_legacy_or_malformed_grant_cannot_authorize_renewal(app, database, tool_registry, user_id):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        candidate = create_delegated_tool_session(
            str(user_id), "example-tool", "example-client", 300
        )
        stored_before = database.tool_sessions.find_one({})

        legacy_code = issuer.issue(
            "example-client",
            session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
        )
        database.tool_launch_grants.update_one(
            {"_id": tool_grants._hash_secret(legacy_code)},
            {"$unset": {"allow_session_renewal": ""}},
        )
        assert (
            exchange_launch_code(
                legacy_code,
                "example-tool",
                "example-client",
                300,
                expected_user_id=str(user_id),
                candidate_tool_access_token=candidate.tool_access_token,
                renew_existing_session=True,
            )
            is None
        )

        malformed_code = issuer.issue(
            "example-client",
            session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            allow_session_renewal=True,
        )
        database.tool_launch_grants.update_one(
            {"_id": tool_grants._hash_secret(malformed_code)},
            {"$set": {"allow_session_renewal": 1}},
        )
        assert (
            exchange_launch_code(
                malformed_code,
                "example-tool",
                "example-client",
                expected_user_id=str(user_id),
            )
            is None
        )
        assert database.tool_sessions.find_one({}) == stored_before


@pytest.mark.parametrize(
    ("created_offset", "expiry_offset"),
    (
        (-1, -1),
        (1, 60),
        (-1, 301),
        (-7 * 24 * 60 * 60, 60),
    ),
)
def test_renewal_never_revives_ineligible_timestamps(
    app,
    database,
    tool_registry,
    user_id,
    monkeypatch,
    created_offset,
    expiry_offset,
):
    fixed_now = datetime(2026, 1, 8, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(tool_grants, "_now", lambda: fixed_now)

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        candidate = create_delegated_tool_session(
            str(user_id), "example-tool", "example-client", 60
        )
        database.tool_sessions.update_one(
            {},
            {
                "$set": {
                    "created_at": fixed_now + timedelta(seconds=created_offset),
                    "expires_at": fixed_now + timedelta(seconds=expiry_offset),
                }
            },
        )

        exchange = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
                allow_session_renewal=True,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=candidate.tool_access_token,
            renew_existing_session=True,
        )

        assert exchange is not None
        assert exchange.session_reused is False
        assert exchange.session_renewed is False
        assert exchange.tool_session.tool_access_token != candidate.tool_access_token


def test_compare_and_set_loss_rereads_authoritative_expiry_once(
    app, database, tool_registry, user_id, monkeypatch
):
    fixed_now = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    monkeypatch.setattr(tool_grants, "_now", lambda: fixed_now)

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        candidate = create_delegated_tool_session(
            str(user_id), "example-tool", "example-client", 60
        )
        collection_type = type(database.tool_sessions)
        original_find_one_and_update = collection_type.find_one_and_update
        compare_and_set_calls = 0
        concurrent_expiry = fixed_now + timedelta(seconds=250)

        def lose_to_concurrent_renewal(collection, query, update, *args, **kwargs):
            nonlocal compare_and_set_calls
            if collection.name != "tool_sessions":
                return original_find_one_and_update(collection, query, update, *args, **kwargs)
            compare_and_set_calls += 1
            collection.update_one(
                {"_id": query["_id"]}, {"$set": {"expires_at": concurrent_expiry}}
            )
            return None

        monkeypatch.setattr(
            collection_type,
            "find_one_and_update",
            lose_to_concurrent_renewal,
        )
        exchange = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
                allow_session_renewal=True,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=candidate.tool_access_token,
            minimum_reuse_lifetime_seconds=200,
            renew_existing_session=True,
        )

        assert exchange is not None
        assert compare_and_set_calls == 1
        assert exchange.session_reused is True
        assert exchange.session_renewed is False
        assert exchange.tool_session.tool_access_token == candidate.tool_access_token
        assert exchange.tool_session.expires_at == concurrent_expiry


def test_interleaved_renewals_report_one_compare_and_set_winner(
    app, database, tool_registry, user_id, monkeypatch
):
    fixed_now = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    monkeypatch.setattr(tool_grants, "_now", lambda: fixed_now)

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        candidate = create_delegated_tool_session(
            str(user_id), "example-tool", "example-client", 60
        )
        first_code = issuer.issue(
            "example-client",
            session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            allow_session_renewal=True,
        )
        second_code = issuer.issue(
            "example-client",
            session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            allow_session_renewal=True,
        )
        collection_type = type(database.tool_sessions)
        original_find_one_and_update = collection_type.find_one_and_update
        interleaving_triggered = False
        second_exchange: tool_grants.ToolLaunchExchange | None = None

        def interleave_second_renewal(collection, query, update, *args, **kwargs):
            nonlocal interleaving_triggered, second_exchange
            if collection.name == "tool_sessions" and not interleaving_triggered:
                interleaving_triggered = True
                second_exchange = exchange_launch_code(
                    second_code,
                    "example-tool",
                    "example-client",
                    300,
                    expected_user_id=str(user_id),
                    candidate_tool_access_token=candidate.tool_access_token,
                    minimum_reuse_lifetime_seconds=200,
                    renew_existing_session=True,
                )
            return original_find_one_and_update(collection, query, update, *args, **kwargs)

        monkeypatch.setattr(
            collection_type,
            "find_one_and_update",
            interleave_second_renewal,
        )
        first_exchange = exchange_launch_code(
            first_code,
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=candidate.tool_access_token,
            minimum_reuse_lifetime_seconds=200,
            renew_existing_session=True,
        )

        assert interleaving_triggered is True
        assert first_exchange is not None
        assert second_exchange is not None
        assert first_exchange.session_reused is True
        assert first_exchange.session_renewed is False
        assert second_exchange.session_reused is True
        assert second_exchange.session_renewed is True
        assert first_exchange.tool_session.expires_at == second_exchange.tool_session.expires_at


@pytest.mark.parametrize("interleaving", ("replacement", "revocation"))
def test_concurrent_replacement_or_revocation_never_revives_candidate(
    app, database, tool_registry, user_id, monkeypatch, interleaving
):
    fixed_now = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    monkeypatch.setattr(tool_grants, "_now", lambda: fixed_now)

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        candidate = create_delegated_tool_session(
            str(user_id), "example-tool", "example-client", 60
        )
        collection_type = type(database.tool_sessions)
        original_find_one_and_update = collection_type.find_one_and_update
        interleaving_triggered = False

        def interleave_session_change(collection, query, update, *args, **kwargs):
            nonlocal interleaving_triggered
            if collection.name == "tool_sessions" and not interleaving_triggered:
                interleaving_triggered = True
                if interleaving == "replacement":
                    create_delegated_tool_session(
                        str(user_id), "example-tool", "replacement-client", 300
                    )
                else:
                    collection.delete_one({"_id": query["_id"]})
            return original_find_one_and_update(collection, query, update, *args, **kwargs)

        monkeypatch.setattr(
            collection_type,
            "find_one_and_update",
            interleave_session_change,
        )
        exchange = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
                allow_session_renewal=True,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=candidate.tool_access_token,
            renew_existing_session=True,
        )

        assert interleaving_triggered is True
        assert exchange is not None
        assert exchange.session_reused is False
        assert exchange.session_renewed is False
        assert exchange.tool_session.tool_access_token != candidate.tool_access_token
        assert get_tool_access_token_user_id(candidate.tool_access_token) is None
        assert database.tool_sessions.count_documents({}) == 1


@pytest.mark.parametrize(
    ("session_policy", "expected_session_count", "candidate_remains_active"),
    (
        (None, 1, False),
        (ToolSessionPolicy.INDEPENDENT, 2, True),
    ),
)
def test_candidate_cannot_select_reuse_without_reuse_grant_policy(
    app,
    database,
    tool_registry,
    user_id,
    session_policy,
    expected_session_count,
    candidate_remains_active,
):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        candidate = create_delegated_tool_session(
            str(user_id),
            "example-tool",
            "example-client",
            300,
        )
        if session_policy is None:
            code = issuer.issue("example-client")
        else:
            code = issuer.issue("example-client", session_policy=session_policy)

        exchange = exchange_launch_code(
            code,
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=candidate.tool_access_token,
        )

        assert exchange is not None
        assert exchange.session_reused is False
        assert exchange.tool_session.tool_access_token != candidate.tool_access_token
        assert database.tool_sessions.count_documents({}) == expected_session_count
        assert (
            get_tool_access_token_user_id(candidate.tool_access_token) is not None
        ) is candidate_remains_active


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("client_id", "wrong-client"),
        ("hash", "wrong-hash"),
        ("type", "wrong-type"),
        ("version", 2),
        ("created_at", "malformed"),
        ("expires_at", "malformed"),
    ),
)
def test_ineligible_reuse_candidate_falls_back_to_replacement(
    app, database, tool_registry, user_id, monkeypatch, field, value
):
    fixed_now = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    monkeypatch.setattr(tool_grants, "_now", lambda: fixed_now)

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        initial = create_delegated_tool_session(
            str(user_id),
            "example-tool",
            "example-client",
            300,
        )
        database.tool_sessions.update_one({}, {"$set": {field: value}})

        exchange = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=initial.tool_access_token,
        )

        assert exchange is not None
        assert exchange.session_reused is False
        assert exchange.tool_session.tool_access_token != initial.tool_access_token
        assert database.tool_sessions.count_documents({}) == 1


@pytest.mark.parametrize("changed_binding", ("user", "tool_id"))
def test_cross_boundary_candidate_falls_back_without_changing_other_sessions(
    app,
    database,
    tool_registry,
    user_id,
    another_user_id,
    monkeypatch,
    changed_binding,
):
    tool_registry.register(OtherExampleTool())
    fixed_now = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    monkeypatch.setattr(tool_grants, "_now", lambda: fixed_now)

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        if changed_binding == "user":
            candidate = create_delegated_tool_session(
                str(another_user_id),
                "example-tool",
                "example-client",
                300,
            )
        else:
            candidate = create_delegated_tool_session(
                str(user_id),
                "other-example-tool",
                "example-client",
                300,
            )

        exchange = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=candidate.tool_access_token,
        )

        assert exchange is not None
        assert exchange.session_reused is False
        assert database.tool_sessions.count_documents({}) == 2
        assert get_tool_access_token_user_id(candidate.tool_access_token) is not None


@pytest.mark.parametrize(
    ("created_offset", "expiry_offset", "minimum_lifetime"),
    (
        (1, 300, 0),
        (-1, -1, 0),
        (-1, 60, 61),
        (-1, 301, 0),
    ),
)
def test_reuse_rejects_invalid_or_out_of_policy_timestamps(
    app,
    database,
    tool_registry,
    user_id,
    monkeypatch,
    created_offset,
    expiry_offset,
    minimum_lifetime,
):
    fixed_now = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    monkeypatch.setattr(tool_grants, "_now", lambda: fixed_now)

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        initial = create_delegated_tool_session(
            str(user_id),
            "example-tool",
            "example-client",
            300,
        )
        database.tool_sessions.update_one(
            {},
            {
                "$set": {
                    "created_at": fixed_now + timedelta(seconds=created_offset),
                    "expires_at": fixed_now + timedelta(seconds=expiry_offset),
                }
            },
        )

        exchange = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=initial.tool_access_token,
            minimum_reuse_lifetime_seconds=minimum_lifetime,
        )

        assert exchange is not None
        assert exchange.session_reused is False
        assert exchange.tool_session.tool_access_token != initial.tool_access_token


def test_independent_sessions_coexist_and_replacement_collapses_them(
    app, database, tool_registry, user_id
):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        browser_exchange = exchange_launch_code(
            issuer.issue(
                "browser-client",
                session_policy=ToolSessionPolicy.INDEPENDENT,
            ),
            "example-tool",
            "browser-client",
            expected_user_id=str(user_id),
        )
        service_exchange = exchange_service_launch_code(
            issuer.issue(
                "service-client",
                session_policy=ToolSessionPolicy.INDEPENDENT,
            ),
            "example-tool",
            "service-client",
        )

        assert browser_exchange is not None
        assert service_exchange is not None
        assert database.tool_sessions.count_documents({}) == 2
        assert all(
            not isinstance(session["_id"], str) for session in database.tool_sessions.find({})
        )
        assert get_tool_access_token_user_id(
            browser_exchange.tool_session.tool_access_token
        ) == str(user_id)
        assert get_tool_access_token_user_id(
            service_exchange.tool_session.tool_access_token
        ) == str(user_id)

        replacement = exchange_launch_code(
            issuer.issue("replacement-client"),
            "example-tool",
            "replacement-client",
            expected_user_id=str(user_id),
        )
        assert replacement is not None
        assert database.tool_sessions.count_documents({}) == 1
        assert (
            get_tool_access_token_user_id(browser_exchange.tool_session.tool_access_token) is None
        )
        assert (
            get_tool_access_token_user_id(service_exchange.tool_session.tool_access_token) is None
        )
        assert get_tool_access_token_user_id(replacement.tool_session.tool_access_token) == str(
            user_id
        )


def test_active_independent_sibling_forces_replacement(app, database, tool_registry, user_id):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        canonical = create_delegated_tool_session(
            str(user_id),
            "example-tool",
            "example-client",
            300,
        )
        independent = exchange_launch_code(
            issuer.issue(
                "independent-client",
                session_policy=ToolSessionPolicy.INDEPENDENT,
            ),
            "example-tool",
            "independent-client",
            expected_user_id=str(user_id),
        )
        assert independent is not None

        exchange = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=canonical.tool_access_token,
        )

        assert exchange is not None
        assert exchange.session_reused is False
        assert database.tool_sessions.count_documents({}) == 1
        assert get_tool_access_token_user_id(canonical.tool_access_token) is None
        assert get_tool_access_token_user_id(independent.tool_session.tool_access_token) is None


def test_expired_independent_sibling_does_not_block_reuse(
    app, database, tool_registry, user_id, monkeypatch
):
    fixed_now = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    monkeypatch.setattr(tool_grants, "_now", lambda: fixed_now)

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        canonical = create_delegated_tool_session(
            str(user_id),
            "example-tool",
            "example-client",
            300,
        )
        independent = exchange_launch_code(
            issuer.issue(
                "independent-client",
                session_policy=ToolSessionPolicy.INDEPENDENT,
            ),
            "example-tool",
            "independent-client",
            300,
            expected_user_id=str(user_id),
        )
        assert independent is not None
        database.tool_sessions.update_one(
            {"client_id": "independent-client"},
            {"$set": {"expires_at": fixed_now - timedelta(seconds=1)}},
        )

        exchange = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=canonical.tool_access_token,
        )

        assert exchange is not None
        assert exchange.session_reused is True
        assert exchange.tool_session.tool_access_token == canonical.tool_access_token
        assert database.tool_sessions.count_documents({}) == 2
        assert get_tool_access_token_user_id(independent.tool_session.tool_access_token) is None


def test_independent_session_is_not_a_reuse_candidate(app, database, tool_registry, user_id):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        independent = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.INDEPENDENT,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
        )
        assert independent is not None

        exchange = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=independent.tool_session.tool_access_token,
        )

        assert exchange is not None
        assert exchange.session_reused is False
        assert exchange.tool_session.tool_access_token != independent.tool_session.tool_access_token
        assert database.tool_sessions.count_documents({}) == 1
        assert get_tool_access_token_user_id(independent.tool_session.tool_access_token) is None


def test_interleaved_replacements_keep_the_last_canonical_write(
    app, database, tool_registry, user_id, monkeypatch
):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        first_code = issuer.issue("example-client")
        second_code = issuer.issue("example-client")
        collection_type = type(database.tool_sessions)
        original_delete_many = collection_type.delete_many
        second_exchange: tool_grants.ToolLaunchExchange | None = None
        interleaving_triggered = False

        def interleaved_delete_many(collection, query, *args, **kwargs):
            nonlocal interleaving_triggered, second_exchange
            result = original_delete_many(collection, query, *args, **kwargs)
            if collection.name == "tool_sessions" and not interleaving_triggered:
                interleaving_triggered = True
                second_exchange = exchange_launch_code(
                    second_code,
                    "example-tool",
                    "example-client",
                    expected_user_id=str(user_id),
                )
            return result

        monkeypatch.setattr(collection_type, "delete_many", interleaved_delete_many)
        first_exchange = exchange_launch_code(
            first_code,
            "example-tool",
            "example-client",
            expected_user_id=str(user_id),
        )

        assert interleaving_triggered is True
        assert first_exchange is not None
        assert second_exchange is not None
        assert database.tool_sessions.count_documents({}) == 1
        assert get_tool_access_token_user_id(first_exchange.tool_session.tool_access_token) == str(
            user_id
        )
        assert get_tool_access_token_user_id(second_exchange.tool_session.tool_access_token) is None


def test_independent_insert_after_reuse_check_survives_until_next_reuse(
    app, database, tool_registry, user_id, monkeypatch
):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        candidate = create_delegated_tool_session(
            str(user_id),
            "example-tool",
            "example-client",
            300,
        )
        original_reuse = tool_grants._reuse_delegated_tool_session
        independent_session: tool_grants.DelegatedToolSession | None = None

        def reuse_then_insert_independent(*args, **kwargs):
            nonlocal independent_session
            reused = original_reuse(*args, **kwargs)
            assert reused is not None
            independent_session = tool_grants._create_independent_delegated_tool_session(
                user_id=str(user_id),
                tool_id="example-tool",
                client_id="independent-client",
                lifetime_seconds=300,
            )
            return reused

        monkeypatch.setattr(
            tool_grants,
            "_reuse_delegated_tool_session",
            reuse_then_insert_independent,
        )
        reused_exchange = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=candidate.tool_access_token,
        )
        monkeypatch.setattr(
            tool_grants,
            "_reuse_delegated_tool_session",
            original_reuse,
        )

        assert reused_exchange is not None
        assert reused_exchange.session_reused is True
        assert independent_session is not None
        assert database.tool_sessions.count_documents({}) == 2
        assert get_tool_access_token_user_id(candidate.tool_access_token) == str(user_id)
        assert get_tool_access_token_user_id(independent_session.tool_access_token) == str(user_id)

        collapsed_exchange = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.REUSE_OR_REPLACE,
            ),
            "example-tool",
            "example-client",
            300,
            expected_user_id=str(user_id),
            candidate_tool_access_token=candidate.tool_access_token,
        )

        assert collapsed_exchange is not None
        assert collapsed_exchange.session_reused is False
        assert collapsed_exchange.tool_session.tool_access_token != candidate.tool_access_token
        assert database.tool_sessions.count_documents({}) == 1
        assert get_tool_access_token_user_id(candidate.tool_access_token) is None
        assert get_tool_access_token_user_id(independent_session.tool_access_token) is None


def test_inactive_user_grant_is_consumed_without_issuing_session(
    app, database, tool_registry, deactivated_user_id
):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(deactivated_user_id))
        code = issuer.issue(
            "example-client",
            session_policy=ToolSessionPolicy.INDEPENDENT,
        )

        assert exchange_service_launch_code(code, "example-tool", "example-client") is None
        assert exchange_service_launch_code(code, "example-tool", "example-client") is None
        assert database.tool_sessions.count_documents({}) == 0


def test_selection_code_accepts_independent_same_user_token_only_once(
    app, tool_registry, user_id, another_user_id
):
    selection = ItemSelection(
        action_id="compare-items",
        item_refcodes=("test:one", "test:two"),
    )

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer("example-tool", str(user_id))
        independent = exchange_launch_code(
            issuer.issue(
                "example-client",
                session_policy=ToolSessionPolicy.INDEPENDENT,
            ),
            "example-tool",
            "example-client",
            expected_user_id=str(user_id),
        )
        unrelated = create_delegated_tool_session(
            str(another_user_id),
            "example-tool",
            "example-client",
        )
        selection_code = issue_tool_selection_code(
            user_id=str(user_id),
            tool_id="example-tool",
            selection=selection,
        )
        assert independent is not None

        assert (
            tool_grants.consume_tool_selection_code(
                code=selection_code,
                tool_id="example-tool",
                tool_access_token=unrelated.tool_access_token,
                expected_user_id=str(another_user_id),
            )
            is None
        )
        assert (
            tool_grants.consume_tool_selection_code(
                code=selection_code,
                tool_id="example-tool",
                tool_access_token=independent.tool_session.tool_access_token,
                expected_user_id=str(user_id),
            )
            == selection
        )
        assert (
            tool_grants.consume_tool_selection_code(
                code=selection_code,
                tool_id="example-tool",
                tool_access_token=independent.tool_session.tool_access_token,
                expected_user_id=str(user_id),
            )
            is None
        )


def test_launch_and_selection_exchanges_are_single_use(app, user_id, tool_registry):
    selection = ItemSelection(
        action_id="compare-items",
        item_refcodes=("test:one", "test:two"),
    )

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer(
            tool_id="example-tool",
            user_id=str(user_id),
            selection=selection,
        )
        launch_code = issuer.issue("example-client")
        exchange = exchange_launch_code(
            launch_code,
            "example-tool",
            "example-client",
            expected_user_id=str(user_id),
        )

        assert exchange is not None
        assert exchange.context.user_id == str(user_id)
        assert exchange.selection == selection
        assert (
            exchange_launch_code(
                launch_code,
                "example-tool",
                "example-client",
                expected_user_id=str(user_id),
            )
            is None
        )

        selection_code = issue_tool_selection_code(
            user_id=str(user_id),
            tool_id="example-tool",
            selection=selection,
        )

    headers = {"DATALAB-API-KEY": exchange.tool_session.tool_access_token}
    app.test_client_class = FlaskClient
    client = app.test_client()
    response = client.post(
        "/tools/example-tool/selection/exchange",
        json={"code": selection_code},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json == {"action": "compare-items", "items": ["test:one", "test:two"]}
    assert response.headers["Cache-Control"] == "no-store"
    assert (
        client.post(
            "/tools/example-tool/selection/exchange",
            json={"code": selection_code},
            headers=headers,
        ).status_code
        == 400
    )


def test_launch_exchange_requires_browser_user_binding(
    app,
    user_id,
    admin_user_id,
    tool_registry,
):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer(
            tool_id="example-tool",
            user_id=str(user_id),
        )
        launch_code = issuer.issue("example-client")

        with pytest.raises(ValueError, match="must not be empty"):
            exchange_launch_code(
                launch_code,
                "example-tool",
                "example-client",
                expected_user_id="",
            )
        assert (
            exchange_launch_code(
                launch_code,
                "example-tool",
                "example-client",
                expected_user_id=str(admin_user_id),
            )
            is None
        )
        exchange = exchange_launch_code(
            launch_code,
            "example-tool",
            "example-client",
            expected_user_id=str(user_id),
        )
        assert exchange is not None
        assert exchange.context.user_id == str(user_id)

        service_exchange = exchange_service_launch_code(
            issuer.issue("example-client"),
            "example-tool",
            "example-client",
        )
        assert service_exchange is not None
        assert service_exchange.context.user_id == str(user_id)


def test_admin_tool_token_uses_restricted_effective_role(
    app,
    admin_user_id,
    tool_registry,
):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer(
            tool_id="example-tool",
            user_id=str(admin_user_id),
        )
        exchange = exchange_launch_code(
            issuer.issue("example-client"),
            "example-tool",
            "example-client",
            expected_user_id=str(admin_user_id),
        )

        assert exchange is not None
        assert exchange.context.role == "user"

        delegated_user = get_by_api_key(exchange.tool_session.tool_access_token)
        assert delegated_user is not None
        assert delegated_user.auth_method is AuthMethod.TOOL_ACCESS_TOKEN
        assert delegated_user.role is UserRole.USER

        delegated_user.refresh()
        assert delegated_user.auth_method is AuthMethod.TOOL_ACCESS_TOKEN
        assert delegated_user.role is UserRole.USER

    app.test_client_class = FlaskClient
    response = app.test_client().get(
        "/get-current-user/",
        headers={"DATALAB-API-KEY": exchange.tool_session.tool_access_token},
    )
    assert response.status_code == 200
    assert response.json["role"] == "user"


def test_admin_tool_token_has_no_implicit_admin_permissions(
    app,
    client,
    admin_user_id,
    tool_registry,
):
    response = client.post(
        "/new-sample/",
        json={"type": "samples", "item_id": "admin-tool-token-private-sample"},
    )
    assert response.status_code == 201
    refcode = response.json["sample_list_entry"]["refcode"]

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer(
            tool_id="example-tool",
            user_id=str(admin_user_id),
        )
        exchange = exchange_launch_code(
            issuer.issue("example-client"),
            "example-tool",
            "example-client",
            expected_user_id=str(admin_user_id),
        )
        assert exchange is not None

    tool_headers = {"DATALAB-API-KEY": exchange.tool_session.tool_access_token}
    app.test_client_class = FlaskClient
    tool_client = app.test_client()

    response = tool_client.get(f"/items/{refcode}?sudo=1", headers=tool_headers)
    assert response.status_code == 404

    response = tool_client.put(
        "/tags",
        json={"data": {"name": "admin-tool-token-global", "scope": "global"}},
        headers=tool_headers,
    )
    assert response.status_code == 403


def test_tool_token_cannot_issue_item_access_token(
    app,
    client,
    database,
    tool_registry,
    user_id,
):
    response = client.post(
        "/new-sample/",
        json={"type": "samples", "item_id": "tool-token-owned-sample"},
    )
    assert response.status_code == 201
    refcode = response.json["sample_list_entry"]["refcode"]

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer(
            tool_id="example-tool",
            user_id=str(user_id),
        )
        exchange = exchange_launch_code(
            issuer.issue("example-client"),
            "example-tool",
            "example-client",
            expected_user_id=str(user_id),
        )
        assert exchange is not None

    item_token_query = {"type": "access_token", "refcode": refcode}
    token_count = database.api_keys.count_documents(item_token_query)

    app.test_client_class = FlaskClient
    response = app.test_client().post(
        f"/items/{refcode}/issue-access-token",
        headers={"DATALAB-API-KEY": exchange.tool_session.tool_access_token},
    )

    assert response.status_code == 403
    assert response.json == {
        "title": "Forbidden",
        "message": (
            "A tool's temporary access cannot be used to create long-lived access to an item."
        ),
        "status": "error",
    }
    assert database.api_keys.count_documents(item_token_query) == token_count


def test_tool_catalog_and_launch_use_browser_session(session_client, tool_registry):
    catalog = session_client.get("/info/tools")

    assert catalog.status_code == 200
    assert catalog.headers["Cache-Control"] == "private, no-store"
    assert catalog.json["data"][0]["id"] == "example-tool"

    launch = session_client.post(
        "/tools/example-tool/launch",
        json={"action": "compare-items", "items": ["test:one", "test:two"]},
        headers={"Origin": "http://localhost"},
    )

    assert launch.status_code == 200
    assert launch.json["url"].startswith("https://tools.example.test/start?code=")


@pytest.mark.parametrize(
    "launch_url",
    (
        "https://tools.example.test/start",
        "http://localhost:8080/start",
        "http://127.42.0.9/start",
        "http://[::1]:8080/start",
    ),
)
def test_tool_launch_accepts_https_and_loopback_http(
    session_client, tool_registry, monkeypatch, launch_url
):
    monkeypatch.setattr(ExampleTool, "launch", lambda self, context, grants: launch_url)

    response = session_client.post(
        "/tools/example-tool/launch",
        json={},
        headers={"Origin": "http://localhost"},
    )

    assert response.status_code == 200
    assert response.json["url"] == launch_url


@pytest.mark.parametrize(
    "launch_result",
    (
        "http://tools.example.test/start?code=must-not-leak",
        "http://localhost.example.com/start",
        "https://user:secret@tools.example.test/start",
        "ftp://tools.example.test/start",
        None,
    ),
)
def test_tool_launch_rejects_unsafe_urls_without_disclosure(
    session_client, tool_registry, monkeypatch, launch_result
):
    monkeypatch.setattr(ExampleTool, "launch", lambda self, context, grants: launch_result)

    response = session_client.post(
        "/tools/example-tool/launch",
        json={},
        headers={"Origin": "http://localhost"},
    )

    assert response.status_code == 503
    assert response.json == {"status": "error", "message": "Unable to launch tool"}
    assert "must-not-leak" not in response.get_data(as_text=True)


def test_tool_launch_allows_insecure_http_only_for_http_urls_without_credentials(
    session_client, tool_registry, monkeypatch
):
    monkeypatch.setattr(CONFIG.TOOLS, "ALLOW_INSECURE_HTTP", True)

    launch_url = "http://tools.example.test/start"
    monkeypatch.setattr(ExampleTool, "launch", lambda self, context, grants: launch_url)
    response = session_client.post(
        "/tools/example-tool/launch",
        json={},
        headers={"Origin": "http://localhost"},
    )
    assert response.status_code == 200
    assert response.json["url"] == launch_url

    for unsafe_url in (
        "http://user:secret@tools.example.test/start",
        "ftp://tools.example.test/start",
    ):
        monkeypatch.setattr(
            ExampleTool,
            "launch",
            lambda self, context, grants, value=unsafe_url: value,
        )
        response = session_client.post(
            "/tools/example-tool/launch",
            json={},
            headers={"Origin": "http://localhost"},
        )
        assert response.status_code == 503
        assert response.json == {"status": "error", "message": "Unable to launch tool"}


def test_tool_launch_uses_read_permissions_for_administrators(
    app, admin_user_id, tool_registry, monkeypatch
):
    observed_permissions = []

    def launch_with_permission_probe(self, context, grants):
        observed_permissions.append(
            get_default_permissions(user_only=False, inherit_from_collections=False)
        )
        return "https://tools.example.test/start"

    monkeypatch.setattr(ExampleTool, "launch", launch_with_permission_probe)

    app.test_client_class = FlaskClient
    with app.test_client() as admin_session_client:
        with admin_session_client.session_transaction() as session:
            session["_user_id"] = str(admin_user_id)

        response = admin_session_client.post(
            "/tools/example-tool/launch",
            json={},
            headers={"Origin": "http://localhost"},
        )
        assert response.status_code == 200
        assert observed_permissions[-1] != {}

        response = admin_session_client.post(
            "/tools/example-tool/launch?sudo=1",
            json={},
            headers={"Origin": "http://localhost"},
        )
        assert response.status_code == 200
        assert observed_permissions[-1] == {}


def test_tool_launch_rejects_api_keys_and_invalid_selections(client, session_client, tool_registry):
    assert client.post("/tools/example-tool/launch", json={}).status_code == 403

    response = session_client.post(
        "/tools/example-tool/launch",
        json={"action": "compare-items", "items": ["test:one"]},
        headers={"Origin": "http://localhost"},
    )
    assert response.status_code == 400
    assert "outside this tool action's limits" in response.json["message"]


def test_disabling_tool_invalidates_delegated_token(
    app, database, tool_registry, user_id, monkeypatch
):
    with app.app_context():
        session = create_delegated_tool_session(str(user_id), "example-tool", "example-client")
        monkeypatch.setattr(CONFIG.TOOLS, "DISABLED", {"example-tool"})
        assert get_tool_access_token_user_id(session.tool_access_token) is None
