"""Tests for the administrator-driven database upgrade framework."""

import pytest
from packaging.version import Version

from pydatalab.upgrade import (
    METADATA_COLLECTION,
    SCHEMA_VERSION_ID,
    DatabaseUpgrader,
    DatabaseVersionStatus,
    NoDocumentsIn,
    UninitialisedDatabaseError,
    UpgradeAction,
    UpgradeConditionsFailedError,
    check_database_version_on_startup,
    code_version,
)

# A marker collection written to by the throwaway test upgrades.
MARKER_COLLECTION = "__upgrade_test_marker__"

# A fixed "code version" the startup-check tests pin onto the upgrader, so they
# exercise the status logic deterministically regardless of the installed
# package version (which is ``None`` on development / setuptools-scm builds).
PINNED_CODE = Version("1.0.0")


@pytest.fixture
def clean_registry():
    """Snapshot and restore the class-level upgrade registries around a test."""
    upgrades = dict(DatabaseUpgrader._upgrade_registry)
    conditions = dict(DatabaseUpgrader._upgrade_conditions_registry)
    DatabaseUpgrader._upgrade_registry.clear()
    DatabaseUpgrader._upgrade_conditions_registry.clear()
    try:
        yield
    finally:
        DatabaseUpgrader._upgrade_registry.clear()
        DatabaseUpgrader._upgrade_registry.update(upgrades)
        DatabaseUpgrader._upgrade_conditions_registry.clear()
        DatabaseUpgrader._upgrade_conditions_registry.update(conditions)


@pytest.fixture(autouse=True)
def clean_collections(database):
    """Drop the collections these tests touch, before and after each test."""
    for coll in (METADATA_COLLECTION, MARKER_COLLECTION, "items"):
        database[coll].delete_many({})
    yield
    for coll in (METADATA_COLLECTION, MARKER_COLLECTION, "items"):
        database[coll].delete_many({})


def _make_marker_upgrade(version: str, conditions=None):
    """Register a throwaway upgrade that writes a marker document."""

    @DatabaseUpgrader.register_upgrade(version, upgrade_conditions=conditions)
    def _upgrade(db, session=None, dry_run=False):
        action = UpgradeAction(
            description=f"Write marker for {version}",
            collection=MARKER_COLLECTION,
            action_type="insert",
            details={"version": version},
            required=True,
        )
        if not dry_run:
            db[MARKER_COLLECTION].insert_one({"version": version}, session=session)
        return [action]

    return _upgrade


# --- code_version() resolution ------------------------------------------------


@pytest.mark.parametrize(
    "version_str, expected",
    [
        # Clean release tags are honoured.
        ("0.8.0", Version("0.8.0")),
        # A genuine post-release (no local segment) is still a release.
        ("0.7.0.post1", Version("0.7.0.post1")),
        # setuptools-scm dev builds carry a local segment -> development.
        ("0.1.0.post1407+g019fc0478", None),
        # An explicit local segment alone is enough -> development.
        ("1.0.0+local", None),
        # A .dev pre-release -> development.
        ("0.8.0.dev3", None),
        # The unparseable fallback used when the package is not installed.
        ("develop", None),
    ],
)
def test_code_version_resolution(monkeypatch, version_str, expected):
    """`code_version()` returns a Version only for real releases, else None."""
    monkeypatch.setattr("pydatalab.upgrade.__version__", version_str)
    assert code_version() == expected


# --- pure version read --------------------------------------------------------


def test_unstamped_db_reads_as_none(database, clean_registry):
    upgrader = DatabaseUpgrader(database)
    assert upgrader.get_db_version() is None
    assert upgrader.is_initialised() is False
    # Reading must not write anything.
    assert database[METADATA_COLLECTION].find_one({"_id": SCHEMA_VERSION_ID}) is None


def test_update_and_read_roundtrip(database, clean_registry):
    upgrader = DatabaseUpgrader(database)
    upgrader.update_db_version(Version("1.2.3"))
    assert upgrader.get_db_version() == Version("1.2.3")
    assert upgrader.is_initialised() is True


# --- initialise (new installation) -------------------------------------------


def test_initialise_records_version_without_running_upgrades(database, clean_registry):
    """initialise() stamps the version and never applies registered upgrades."""
    _make_marker_upgrade("99.0.0")
    upgrader = DatabaseUpgrader(database)

    recorded = upgrader.initialise(version="50.0.0")

    assert recorded == Version("50.0.0")
    assert upgrader.get_db_version() == Version("50.0.0")
    # The registered upgrade must NOT have run.
    assert database[MARKER_COLLECTION].count_documents({}) == 0


def test_initialise_refuses_when_already_initialised(database, clean_registry):
    upgrader = DatabaseUpgrader(database)
    upgrader.initialise(version="1.0.0")

    with pytest.raises(RuntimeError):
        upgrader.initialise(version="2.0.0")

    assert upgrader.get_db_version() == Version("1.0.0")

    # force overwrites.
    assert upgrader.initialise(version="2.0.0", force=True) == Version("2.0.0")
    assert upgrader.get_db_version() == Version("2.0.0")


def test_initialise_defaults_to_code_version(database, clean_registry):
    upgrader = DatabaseUpgrader(database)
    upgrader.current_version = PINNED_CODE
    recorded = upgrader.initialise()
    assert recorded == PINNED_CODE


# --- collect / dry-run / upgrade ---------------------------------------------


def test_collect_upgrades(database, clean_registry):
    _make_marker_upgrade("1.0.0")
    _make_marker_upgrade("2.0.0")
    _make_marker_upgrade("3.0.0")
    upgrader = DatabaseUpgrader(database)

    assert upgrader.collect_upgrades(Version("1.0.0"), Version("3.0.0")) == [
        Version("2.0.0"),
        Version("3.0.0"),
    ]
    assert upgrader.collect_upgrades(Version("2.0.0"), Version("2.0.0")) == []


def test_dry_run_makes_no_changes(database, clean_registry):
    _make_marker_upgrade("99.0.0")
    upgrader = DatabaseUpgrader(database)
    upgrader.update_db_version(Version("98.0.0"))

    actions, failed = upgrader.dry_run(target_version="99.0.0")

    assert failed == []
    assert any(a.collection == MARKER_COLLECTION for a in actions)
    assert any(a.collection == METADATA_COLLECTION for a in actions)
    # Nothing was actually written.
    assert database[MARKER_COLLECTION].count_documents({}) == 0
    assert upgrader.get_db_version() == Version("98.0.0")


def test_upgrade_applies_and_records_version(database, clean_registry):
    _make_marker_upgrade("99.0.0")
    upgrader = DatabaseUpgrader(database)
    upgrader.update_db_version(Version("98.0.0"))

    assert upgrader.upgrade(target_version="99.0.0") is True

    assert database[MARKER_COLLECTION].count_documents({"version": "99.0.0"}) == 1
    assert upgrader.get_db_version() == Version("99.0.0")


def test_upgrade_noop_when_already_at_target(database, clean_registry):
    _make_marker_upgrade("99.0.0")
    upgrader = DatabaseUpgrader(database)
    upgrader.update_db_version(Version("99.0.0"))

    assert upgrader.upgrade(target_version="99.0.0") is False
    assert database[MARKER_COLLECTION].count_documents({}) == 0


# --- unstamped database: must not guess --------------------------------------


def test_upgrade_unstamped_with_pending_raises(database, clean_registry):
    """An unstamped DB with applicable upgrades refuses to run without a decision."""
    _make_marker_upgrade("99.0.0")
    upgrader = DatabaseUpgrader(database)

    with pytest.raises(UninitialisedDatabaseError):
        upgrader.upgrade(target_version="99.0.0")

    # Nothing applied or recorded.
    assert database[MARKER_COLLECTION].count_documents({}) == 0
    assert upgrader.get_db_version() is None


def test_upgrade_unstamped_with_from_version_applies(database, clean_registry):
    """Declaring --from-version lets an unstamped (pre-versioning) DB upgrade."""
    _make_marker_upgrade("99.0.0")
    upgrader = DatabaseUpgrader(database)

    assert upgrader.upgrade(from_version="98.0.0", target_version="99.0.0") is True
    assert database[MARKER_COLLECTION].count_documents({"version": "99.0.0"}) == 1
    assert upgrader.get_db_version() == Version("99.0.0")


def test_upgrade_unstamped_no_applicable_upgrades_just_stamps(database, clean_registry):
    """With nothing that could apply, an unstamped DB is simply stamped (no guess needed)."""
    _make_marker_upgrade("99.0.0")
    upgrader = DatabaseUpgrader(database)

    # Target below the registered upgrade -> nothing in range -> safe.
    assert upgrader.upgrade(target_version="1.0.0") is True
    assert database[MARKER_COLLECTION].count_documents({}) == 0
    assert upgrader.get_db_version() == Version("1.0.0")


def test_from_version_contradicting_stamp_refuses(database, clean_registry):
    """--from-version must not override a recorded version (risk of re-running upgrades)."""
    _make_marker_upgrade("99.0.0")
    upgrader = DatabaseUpgrader(database)
    upgrader.update_db_version(Version("98.0.0"))

    with pytest.raises(RuntimeError, match="contradicts"):
        upgrader.upgrade(from_version="0.5.0", target_version="99.0.0")

    assert database[MARKER_COLLECTION].count_documents({}) == 0
    assert upgrader.get_db_version() == Version("98.0.0")


def test_from_version_matching_stamp_is_allowed(database, clean_registry):
    _make_marker_upgrade("99.0.0")
    upgrader = DatabaseUpgrader(database)
    upgrader.update_db_version(Version("98.0.0"))

    assert upgrader.upgrade(from_version="98.0.0", target_version="99.0.0") is True
    assert upgrader.get_db_version() == Version("99.0.0")


# --- audit trail ----------------------------------------------------------------


def test_history_audit_trail(database, clean_registry):
    """Every stamp appends a history entry with version, action and timestamp."""
    _make_marker_upgrade("98.5.0")
    _make_marker_upgrade("99.0.0")
    upgrader = DatabaseUpgrader(database)
    upgrader.initialise(version="98.0.0")

    assert upgrader.upgrade(target_version="99.0.0") is True

    doc = database[METADATA_COLLECTION].find_one({"_id": SCHEMA_VERSION_ID})
    assert [(h["version"], h["action"]) for h in doc["history"]] == [
        ("98.0.0", "initialise"),
        ("98.5.0", "upgrade"),
        ("99.0.0", "upgrade"),
    ]
    assert all("timestamp" in h and "datalab_version" in h for h in doc["history"])


def test_auto_stamp_recorded_in_history(database, clean_registry):
    upgrader = DatabaseUpgrader(database)
    upgrader.current_version = PINNED_CODE

    assert upgrader.check_and_stamp_version() is DatabaseVersionStatus.AUTO_STAMPED

    doc = database[METADATA_COLLECTION].find_one({"_id": SCHEMA_VERSION_ID})
    assert doc["history"][-1]["action"] == "auto_stamp"


# --- preconditions ------------------------------------------------------------


def test_failed_precondition_blocks_upgrade(database, clean_registry):
    database.items.insert_one({"type": "samples", "item_id": "x"})
    condition = NoDocumentsIn(collection="items")
    _make_marker_upgrade("99.0.0", conditions=[condition])
    upgrader = DatabaseUpgrader(database)
    upgrader.update_db_version(Version("98.0.0"))

    with pytest.raises(UpgradeConditionsFailedError):
        upgrader.upgrade(target_version="99.0.0")

    assert database[MARKER_COLLECTION].count_documents({}) == 0
    assert upgrader.get_db_version() == Version("98.0.0")


def test_skippable_precondition_bypassed_with_force(database, clean_registry):
    database.items.insert_one({"type": "samples", "item_id": "x"})
    condition = NoDocumentsIn(collection="items", skippable=True)
    _make_marker_upgrade("99.0.0", conditions=[condition])
    upgrader = DatabaseUpgrader(database)
    upgrader.update_db_version(Version("98.0.0"))

    _, failed = upgrader.dry_run(target_version="99.0.0")
    assert failed
    assert upgrader.upgrade(target_version="99.0.0", force=True) is True
    assert database[MARKER_COLLECTION].count_documents({"version": "99.0.0"}) == 1


def test_open_transaction_does_not_raise(database, clean_registry):
    _make_marker_upgrade("99.0.0")
    upgrader = DatabaseUpgrader(database)
    upgrader.update_db_version(Version("98.0.0"))

    with upgrader.open_transaction() as session:
        assert session is None or session is not None  # never raises

    assert upgrader.upgrade(target_version="99.0.0") is True


# --- startup version check ----------------------------------------------------


def test_check_and_stamp_version_current(database, clean_registry):
    upgrader = DatabaseUpgrader(database)
    upgrader.current_version = PINNED_CODE
    upgrader.update_db_version(PINNED_CODE)
    assert upgrader.check_and_stamp_version() is DatabaseVersionStatus.CURRENT


def test_check_and_stamp_version_ahead(database, clean_registry):
    upgrader = DatabaseUpgrader(database)
    upgrader.current_version = PINNED_CODE
    upgrader.update_db_version(Version("999.0.0"))
    assert upgrader.check_and_stamp_version() is DatabaseVersionStatus.AHEAD


def test_check_and_stamp_version_unstamped_no_upgrades_auto_stamps(database, clean_registry):
    """The framework-introduction release: nothing registered -> auto-stamp current."""
    upgrader = DatabaseUpgrader(database)
    upgrader.current_version = PINNED_CODE

    assert upgrader.check_and_stamp_version() is DatabaseVersionStatus.AUTO_STAMPED
    assert upgrader.get_db_version() == PINNED_CODE


def test_check_and_stamp_version_unstamped_with_upgrades_is_uninitialised(database, clean_registry):
    """An unstamped DB on a release that has upgrades must be disambiguated."""
    upgrader = DatabaseUpgrader(database)
    upgrader.current_version = PINNED_CODE
    # An upgrade in (baseline, code] makes the unstamped state ambiguous.
    _make_marker_upgrade("0.0.1")

    assert upgrader.check_and_stamp_version() is DatabaseVersionStatus.UNINITIALISED
    # No auto-stamp, no upgrade applied.
    assert upgrader.get_db_version() is None
    assert database[MARKER_COLLECTION].count_documents({}) == 0


def test_check_and_stamp_version_behind_with_upgrades_pending(database, clean_registry):
    upgrader = DatabaseUpgrader(database)
    upgrader.current_version = PINNED_CODE
    upgrader.update_db_version(Version("0.0.1"))
    _make_marker_upgrade("0.0.5")  # in (0.0.1, code]

    assert upgrader.check_and_stamp_version() is DatabaseVersionStatus.UPGRADE_PENDING
    # Pending check does not apply the upgrade or move the version.
    assert upgrader.get_db_version() == Version("0.0.1")
    assert database[MARKER_COLLECTION].count_documents({}) == 0


def test_check_and_stamp_version_behind_no_upgrades_auto_stamps(database, clean_registry):
    upgrader = DatabaseUpgrader(database)
    upgrader.current_version = PINNED_CODE
    upgrader.update_db_version(Version("0.0.1"))

    assert upgrader.check_and_stamp_version() is DatabaseVersionStatus.AUTO_STAMPED
    assert upgrader.get_db_version() == PINNED_CODE


def test_startup_helper_returns_status(database, clean_registry):
    # On a development build this resolves to DEV; on a release build to a real
    # status. Either way the helper returns a DatabaseVersionStatus.
    status = check_database_version_on_startup(database)
    assert isinstance(status, DatabaseVersionStatus)
