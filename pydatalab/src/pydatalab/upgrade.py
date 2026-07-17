"""Administrator-driven database upgrades for backward-incompatible changes.

This module provides the machinery for applying *backward-incompatible* changes
to the database when a datalab deployment is upgraded to a new version. The
intended workflow is to stop the server, run ``invoke migration.upgrade`` on a
host with access to the database, and then start the new version.

To register an upgrade, decorate a function with
:meth:`DatabaseUpgrader.register_upgrade`. The function receives the database
handle, an optional session (for transactions), and a ``dry_run`` flag, and must
return the list of :class:`UpgradeAction` it performed (or would have performed,
when ``dry_run`` is set).
"""

from __future__ import annotations

import contextlib
import enum
import functools
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, ClassVar

from packaging.version import InvalidVersion, Version
from packaging.version import parse as parse_version

from pydatalab import __version__
from pydatalab.logger import LOGGER
from pydatalab.mongo import METADATA_COLLECTION

if TYPE_CHECKING:
    import pymongo.database
    from pymongo.client_session import ClientSession

# ``_id`` of the document (in :data:`~pydatalab.mongo.METADATA_COLLECTION`) that
# holds the database schema version.
SCHEMA_VERSION_ID = "datalab_schema_version"
# Sentinel "start of history" used as the lower bound when collecting upgrades
# for a database whose starting version is not otherwise known.
BASELINE_VERSION = Version("0.0.0")


class UpgradeConditionsFailedError(Exception):
    """Raised when an upgrade is blocked because its preconditions are not satisfied."""


class UninitialisedDatabaseError(RuntimeError):
    """Raised when an operation needs a recorded schema version but none exists.

    An unstamped database is ambiguous: it could be a pristine new installation
    (which must be stamped at the current version with no upgrades applied) or an
    existing database from before schema versioning (which may need upgrades).
    The system never guesses between these; the operator must disambiguate with
    ``admin.initialise-schema-version`` (new install) or
    ``migration.upgrade --from-version`` (existing database).
    """


class DatabaseVersionStatus(enum.Enum):
    """Outcome of comparing the recorded schema version with the code version."""

    #: Development install (code version unknown); no check performed.
    DEV = "dev"
    #: Recorded version matches the code version.
    CURRENT = "current"
    #: Version was missing or behind but nothing needed applying, so it was
    #: stamped to the current version automatically.
    AUTO_STAMPED = "auto_stamped"
    #: Recorded version is behind and registered upgrades need to be applied.
    UPGRADE_PENDING = "upgrade_pending"
    #: No version recorded and upgrades exist: the operator must initialise or
    #: upgrade explicitly (see :class:`UninitialisedDatabaseError`).
    UNINITIALISED = "uninitialised"
    #: Recorded version is newer than the code (e.g. an attempted downgrade).
    AHEAD = "ahead"


def code_version() -> Version | None:
    """The version of the installed ``datalab-server`` package.

    Returns ``None`` for development builds. A build is considered "development"
    when the version cannot be parsed or is_devrelease.
    """
    try:
        version = parse_version(__version__)
    except InvalidVersion:
        return None
    if version.local is not None or version.is_devrelease:
        return None
    return version


@dataclass
class UpgradeAction:
    """Details of a single upgrade action to be performed."""

    description: str
    collection: str
    action_type: str
    details: dict
    required: bool = False


# Declared ``kw_only`` so that subclasses can introduce required fields.
@dataclass(kw_only=True)
class UpgradeCondition:
    """A generic precondition that must hold before an upgrade can be applied."""

    description: str
    check_func: Callable[[DatabaseUpgrader, UpgradeCondition], dict | None] | None = None
    skippable: bool = False

    def check(self, upgrader: DatabaseUpgrader) -> dict | None:
        if self.check_func is None:
            raise NotImplementedError("check_func must be defined")
        result = self.check_func(upgrader, self)
        if result and self.skippable:
            result["message"] += (
                " This condition can be bypassed by running the upgrade with the `--force` option."
            )
        return result


@dataclass(kw_only=True)
class NoDocumentsIn(UpgradeCondition):
    """Condition: a collection must contain no document matching a query."""

    collection: str
    query: dict | None = None
    description: str = None  # type: ignore[assignment]

    def __post_init__(self):
        if not self.description:
            q_str = f" matching {self.query}" if self.query else ""
            self.description = (
                f"There should be no document in the '{self.collection}' collection{q_str}"
            )

        def _check(upgrader: DatabaseUpgrader, _condition: UpgradeCondition) -> dict | None:
            count = upgrader.db[self.collection].count_documents(self.query or {})
            if count == 0:
                return None
            return {
                "condition": self,
                "message": f"Found {count} document(s)",
                "count": count,
            }

        self.check_func = _check


class DatabaseUpgrader:
    """Handles upgrading the datalab database between versions.

    Upgrade functions are registered against the version that introduces the
    backward-incompatible change via :meth:`register_upgrade`. When run, the
    upgrader collects every registered upgrade between the database's current
    schema version and the target version and applies them in order, recording
    the new version in the database after each step.
    """

    _upgrade_registry: ClassVar[dict[Version, Callable]] = {}
    _upgrade_conditions_registry: ClassVar[dict[Version, list[UpgradeCondition]]] = {}

    def __init__(self, db: pymongo.database.Database):
        self.db = db
        self.current_version = code_version()
        self._supports_transactions: bool | None = None

    @classmethod
    def register_upgrade(
        cls, version: str, upgrade_conditions: list[UpgradeCondition] | None = None
    ):
        """Decorator registering an upgrade function for the given version.

        Parameters:
            version: The version that introduces the change handled by ``func``.
            upgrade_conditions: Preconditions that must hold before the upgrade
                can be applied.
        """

        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                LOGGER.info("Executing upgrade to version %s", version)
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                LOGGER.info("Completed upgrade to %s in %.2fs", version, duration)
                return result

            vv = parse_version(version)
            cls._upgrade_registry[vv] = wrapper
            if upgrade_conditions:
                cls._upgrade_conditions_registry[vv] = upgrade_conditions
            return wrapper

        return decorator

    @property
    def registered_upgrades(self) -> list[Version]:
        return sorted(self._upgrade_registry.keys())

    def get_db_version(self) -> Version | None:
        """Return the schema version recorded in the database, or ``None``.

        This is a pure read: it never infers a version from database contents and
        never writes. ``None`` means the database has no recorded schema version
        (see :class:`UninitialisedDatabaseError`).
        """
        doc = self.db[METADATA_COLLECTION].find_one({"_id": SCHEMA_VERSION_ID})
        if doc and doc.get("version"):
            return parse_version(doc["version"])
        return None

    def is_initialised(self) -> bool:
        """Whether the database has a recorded schema version."""
        return self.get_db_version() is not None

    def update_db_version(
        self,
        version: Version,
        session: ClientSession | None = None,
        action: str = "upgrade",
    ) -> None:
        """Record ``version`` as the database schema version.

        Every write also appends an entry to the ``history`` array of the metadata
        document (version, action, timestamp and the running datalab version), as
        an audit trail of how the recorded version evolved.

        Parameters:
            version: The version to record.
            session: Optional session when running inside a transaction.
            action: What caused the write: ``"upgrade"``, ``"initialise"`` or
                ``"auto_stamp"``.
        """
        history_entry = {
            "version": str(version),
            "action": action,
            "timestamp": datetime.now(timezone.utc),
            "datalab_version": __version__,
        }
        self.db[METADATA_COLLECTION].update_one(
            {"_id": SCHEMA_VERSION_ID},
            {
                "$set": {"version": str(version)},
                "$push": {"history": history_entry},
            },
            upsert=True,
            session=session,
        )

    def supports_transactions(self) -> bool:
        """Whether the connected MongoDB supports multi-document transactions.

        Transactions require a replica set (or sharded cluster); datalab can also
        run against a standalone ``mongod``, where they are unavailable.
        """
        if self._supports_transactions is None:
            try:
                hello = self.db.client.admin.command("hello")
                self._supports_transactions = bool(
                    hello.get("setName") or hello.get("msg") == "isdbgrid"
                )
            except Exception:
                self._supports_transactions = False
        return self._supports_transactions

    @contextlib.contextmanager
    def open_transaction(self):
        """Yield a transaction session if supported, otherwise yield ``None``."""
        if self.supports_transactions():
            with (
                self.db.client.start_session() as session,
                session.start_transaction(),
            ):
                yield session
        else:
            yield None

    def collect_upgrades(self, from_version: Version, target_version: Version) -> list[Version]:
        """Versions with a registered upgrade in ``(from_version, target_version]``."""
        return [v for v in self.registered_upgrades if from_version < v <= target_version]

    def check_upgrade_conditions(
        self, versions: list[Version], force: bool = False
    ) -> list[tuple[Version, dict]]:
        """Return any failed preconditions for the given ``versions``."""
        failed_conditions = []
        for version in versions:
            for condition in self._upgrade_conditions_registry.get(version, []):
                if force and condition.skippable:
                    continue
                if (check := condition.check(self)) is not None:
                    failed_conditions.append((version, check))
        return failed_conditions

    def _resolve_target(self, target_version: str | None) -> Version:
        """The version to upgrade towards (explicit, else the code version)."""
        if target_version:
            return parse_version(target_version)
        if self.current_version is not None:
            return self.current_version
        # Development install with no explicit target: aim at the last upgrade.
        return self.registered_upgrades[-1] if self.registered_upgrades else BASELINE_VERSION

    def _resolve_versions(
        self, from_version: str | None, target_version: str | None
    ) -> tuple[Version, Version]:
        """Resolve the (from, target) versions for an upgrade.

        The starting version is the recorded schema version. If the database is
        unstamped and no explicit ``from_version`` is given, this raises
        :class:`UninitialisedDatabaseError` *unless* no registered upgrade could
        apply anyway (e.g. the release that first introduces this framework), in
        which case :data:`BASELINE_VERSION` is used and the upgrade simply records
        the target version without applying anything.

        An explicit ``from_version`` exists solely to disambiguate an *unstamped*
        pre-versioning database; if it contradicts a recorded version this raises
        ``RuntimeError`` rather than re-running upgrades that may already have
        been applied.
        """
        target = self._resolve_target(target_version)
        stamped = self.get_db_version()

        if from_version:
            explicit = parse_version(from_version)
            if stamped is not None and stamped != explicit:
                raise RuntimeError(
                    f"--from-version={explicit} contradicts the schema version "
                    f"recorded in the database ({stamped}). The recorded version is "
                    "used automatically, so --from-version is only needed for a "
                    "database with no recorded version. If the recorded version is "
                    "wrong, fix it explicitly with "
                    "`invoke admin.initialise-schema-version --force` first."
                )
            return explicit, target

        if stamped is not None:
            return stamped, target

        # Unstamped and no explicit starting point: only safe to proceed if there
        # is nothing that could be applied; otherwise the operator must decide.
        if self.collect_upgrades(BASELINE_VERSION, target):
            raise UninitialisedDatabaseError(
                "The database has no recorded schema version. If this is a new "
                "installation, run `invoke admin.initialise-schema-version`. If "
                "this is an existing database, run `invoke migration.upgrade "
                "--from-version=<the datalab version it last ran>`."
            )
        return BASELINE_VERSION, target

    def initialise(self, version: str | None = None, force: bool = False) -> Version:
        """Record the schema version *without applying any upgrades*.

        This is the new-installation path: a pristine database is stamped at the
        current code version (or an explicit ``version``) so that subsequent
        upgrades are computed from the right point.

        Raises:
            RuntimeError: if the database is already initialised and ``force`` is
                not set, or if the version cannot be determined.
        """
        target = parse_version(version) if version else self.current_version
        if target is None:
            raise RuntimeError(
                "Cannot determine the version to initialise to on a development "
                "install; pass an explicit version."
            )
        existing = self.get_db_version()
        if existing is not None and not force:
            raise RuntimeError(
                f"Database is already initialised at version {existing}. "
                "Pass force=True to overwrite the recorded version."
            )
        self.update_db_version(target, action="initialise")
        LOGGER.info("Recorded database schema version as %s.", target)
        return target

    def check_and_stamp_version(self) -> DatabaseVersionStatus:
        """Compare the recorded version with the code version (startup check).

        Updates the version in the DB to the current version only when it is safe,
        i.e. when the database is unstamped or behind but no registered upgrade
        falls in the range, so nothing could be skipped.
        Never applies upgrades and never guesses an unstamped database is current
        when upgrades exist.
        """
        code = self.current_version
        if code is None:
            return DatabaseVersionStatus.DEV

        stamped = self.get_db_version()
        if stamped is None:
            if self.collect_upgrades(BASELINE_VERSION, code):
                return DatabaseVersionStatus.UNINITIALISED
            # If there are no upgrades available yet, it is safe to set the
            # version in the db.
            self.update_db_version(code, action="auto_stamp")
            return DatabaseVersionStatus.AUTO_STAMPED

        if stamped == code:
            return DatabaseVersionStatus.CURRENT
        if stamped > code:
            return DatabaseVersionStatus.AHEAD
        # stamped < code
        if self.collect_upgrades(stamped, code):
            return DatabaseVersionStatus.UPGRADE_PENDING
        # DB is stamped, but no upgrades available for the current version of the code.
        # safe to upgrade the DB version automatically.
        self.update_db_version(code, action="auto_stamp")
        return DatabaseVersionStatus.AUTO_STAMPED

    def dry_run(
        self,
        from_version: str | None = None,
        target_version: str | None = None,
        force: bool = False,
    ) -> tuple[list[UpgradeAction], list[tuple[Version, dict]]]:
        """Simulate the upgrade, returning the actions and any failed conditions.

        Makes no changes to the database.
        """
        db_version, target = self._resolve_versions(from_version, target_version)
        if db_version >= target:
            return [], []

        versions_needing_upgrade = self.collect_upgrades(db_version, target)
        failed_conditions = self.check_upgrade_conditions(versions_needing_upgrade, force=force)

        all_actions: list[UpgradeAction] = []
        for version in versions_needing_upgrade:
            all_actions.extend(self._upgrade_registry[version](self.db, dry_run=True))

        all_actions.append(
            UpgradeAction(
                description=f"Update database schema version to {target}",
                collection=METADATA_COLLECTION,
                action_type="update",
                details={
                    "filter": {"_id": SCHEMA_VERSION_ID},
                    "update": {"$set": {"version": str(target)}},
                    "upsert": True,
                },
            )
        )
        return all_actions, failed_conditions

    def upgrade(
        self,
        from_version: str | None = None,
        target_version: str | None = None,
        force: bool = False,
    ) -> bool:
        """Apply the database upgrades from the current to the target version.

        Returns ``True`` if any upgrade was applied, ``False`` if the database
        was already at the target version. Raises
        :class:`UpgradeConditionsFailedError` if any precondition is not satisfied.
        """
        db_version, target = self._resolve_versions(from_version, target_version)
        if db_version >= target:
            LOGGER.info("Database is already at version %s; nothing to upgrade.", db_version)
            return False

        versions_needing_upgrade = self.collect_upgrades(db_version, target)

        if failed_conditions := self.check_upgrade_conditions(
            versions_needing_upgrade, force=force
        ):
            err = ["Some upgrade conditions were not satisfied:"]
            for vv, failed in failed_conditions:
                err.append(
                    f" - {failed['condition'].description} (for version {vv}): {failed['message']}"
                )
            message = "\n".join(err)
            LOGGER.error(message)
            raise UpgradeConditionsFailedError(message)

        LOGGER.info("Starting upgrade from version %s to %s", db_version, target)
        for version in versions_needing_upgrade:
            with self.open_transaction() as session:
                LOGGER.info("Applying upgrade to version %s", version)
                self._upgrade_registry[version](self.db, session=session)
                self.update_db_version(version, session=session)

        # Record the final target version (covers the case where the target is
        # ahead of the last registered upgrade); skip it when the last applied
        # upgrade already recorded exactly the target version.
        if not versions_needing_upgrade or versions_needing_upgrade[-1] != target:
            self.update_db_version(target)
        LOGGER.info("Database upgrade completed successfully (now at %s).", target)
        return True


def check_database_version_on_startup(db: pymongo.database.Database) -> DatabaseVersionStatus:
    """Run the startup schema-version check and log guidance as needed.

    Does not raise. It auto-stamps the current version only when provably safe,
    and otherwise logs an actionable message. Returns the resolved status.
    """
    upgrader = DatabaseUpgrader(db)
    try:
        status = upgrader.check_and_stamp_version()
    except Exception as exc:
        LOGGER.warning("Could not check the database schema version: %s", exc)
        return DatabaseVersionStatus.DEV

    if status is DatabaseVersionStatus.UPGRADE_PENDING:
        LOGGER.warning(
            "\n"
            "============================================================\n"
            "A DATABASE UPGRADE IS PENDING for this datalab version.\n"
            "The server will keep running, but some data may fail to load\n"
            "until you stop the server and run:\n"
            "    invoke migration.upgrade\n"
            "Take a backup first with `invoke admin.create-backup`.\n"
            "============================================================"
        )
    elif status is DatabaseVersionStatus.UNINITIALISED:
        LOGGER.warning(
            "\n"
            "============================================================\n"
            "The database has no recorded schema version.\n"
            "  - New installation? Run:  invoke admin.initialise-schema-version\n"
            "  - Existing database?      invoke migration.upgrade \\\n"
            "                                --from-version=<previous datalab version>\n"
            "The server will keep running in the meantime.\n"
            "============================================================"
        )
    elif status is DatabaseVersionStatus.AHEAD:
        LOGGER.warning(
            "The recorded database schema version is newer than this datalab "
            "version. This server may be running an older release than the one "
            "that last wrote the database."
        )

    return status


# ---------------------------------------------------------------------------
# Registered upgrades
#
# Add backward-incompatible upgrades below using the
# ``@DatabaseUpgrader.register_upgrade("<version>")`` decorator. Each function
# takes ``(db, session=None, dry_run=False)`` and returns the list of
# ``UpgradeAction`` it performed. There are currently no registered upgrades.
# ---------------------------------------------------------------------------
