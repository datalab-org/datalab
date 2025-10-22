import datetime
import subprocess
import tarfile
import tempfile
from pathlib import Path

from pydatalab.config import CONFIG, BackupStrategy
from pydatalab.logger import LOGGER


def take_snapshot(snapshot_path: Path, encrypt: bool = False) -> None:
    """Make a compressed snapshot of the entire datalab deployment that
    can be restored from with sufficient granularity, e.g., including
    config files.

    Creates a tar file with the following structure:
        - `./files/` - contains all files in `CONFIG.FILE_DIRECTORY`
        - `./mongodb/` - contains a dump of the mongodb database
        - `./config/` - contains a dump of the server config

    Arguments:
        snapshot_path: Desired path to the .tar or .tar.gz output file, will raise
            a `FileExistsError` error if the file already exists.
        encrypt: Whether to encrypt the snapshot on write.

    """
    if snapshot_path.exists():
        raise FileExistsError(f"Not overwriting existing file at {snapshot_path}")

    if encrypt:
        raise NotImplementedError("Snapshot encryption not yet implemented")

    if "".join(snapshot_path.suffixes) == ".tar.gz":
        mode = "w:gz"
    elif snapshot_path.suffixes == ".tar":
        mode = "w"
    else:
        raise RuntimeError(
            f"Output path should either be a .tar or .tar.gz file, not {snapshot_path} with {snapshot_path.suffix}"
        )

    LOGGER.info("Creating snapshot of entire datalab instance.")
    LOGGER.debug("Creating snapshot of %s", CONFIG.FILE_DIRECTORY)
    # Add contents of `CONFIG.FILE_DIRECTORY` to the tar file
    with tarfile.open(snapshot_path, mode=mode) as tar:  # type: ignore[call-overload]
        for file in Path(CONFIG.FILE_DIRECTORY).iterdir():
            tar.add(file, arcname=Path("files") / file.relative_to(CONFIG.FILE_DIRECTORY))

        LOGGER.debug("Snapshot of %s created.", CONFIG.FILE_DIRECTORY)

        # Take a database dump and add it to the tar file
        LOGGER.debug("Taking dump of database %s", CONFIG.MONGO_URI)

        # Check that mongodump is available
        subprocess.check_output(["mongodump", "--version"])  # noqa: S603, S607

        with tempfile.TemporaryDirectory() as temp_dir:
            command = ["mongodump", CONFIG.MONGO_URI, "--out", str(Path(temp_dir).resolve())]
            subprocess.check_output(command)  # noqa: S603

            for file in Path(temp_dir).iterdir():
                tar.add(file, arcname=Path("mongodb"))

        LOGGER.debug("Dump of database %s created.", CONFIG.MONGO_URI)

        LOGGER.debug("Dumping server config.")
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(tmp_config := Path(temp_dir) / "config.json", "w") as f:
                data = CONFIG.json(indent=2, exclude_unset=True)
                f.write(data)

                tar.add(
                    tmp_config,
                    arcname=Path("config") / "config.json",
                )
        LOGGER.debug("Config dump created.")
        LOGGER.info("Snapshot saved at %s", snapshot_path)


def restore_snapshot(snapshot_path: Path, decrypt: bool = False):
    """Restore a snapshot created with `make_snapshot` to the current
    datalab instance, using the current configuration.

    This will overwrite the contents of any existing MongoDB of the same
    name.

    Arguments:
        snapshot_path: Path to the .tar or .tar.gz snapshot file.

    """
    LOGGER.info("Attempting to restore snapshot from %s", snapshot_path)
    if decrypt:
        raise NotImplementedError("Snapshot decryption not yet implemented")
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot file not found at {snapshot_path}")

    if "".join(snapshot_path.suffixes) == ".tar.gz":
        mode = "r:gz"
    elif snapshot_path.suffixes == ".tar":
        mode = "r"
    else:
        raise RuntimeError(
            f"Snapshot path should either be a .tar or .tar.gz file, not {snapshot_path} with {snapshot_path.suffix}"
        )

    with tarfile.open(snapshot_path, mode=mode) as tar:  # type: ignore[call-overload]
        LOGGER.debug("Restoring files from %s", snapshot_path)
        files = [m for m in tar.getmembers() if m.name.startswith("files/")]
        tar.extractall(path=CONFIG.FILE_DIRECTORY, members=files)  # noqa: S202
        LOGGER.debug("Files restored from %s", snapshot_path)

        LOGGER.debug("Restoring database from %s", snapshot_path)
        with tempfile.TemporaryDirectory() as temp_dir:
            database = [m for m in tar.getmembers() if m.name.startswith("mongodb/")]
            tar.extractall(path=temp_dir, members=database)  # noqa: S202
            command = ["mongorestore", CONFIG.MONGO_URI, "--drop", str(Path(temp_dir) / "mongodb")]
            subprocess.check_output(command)  # noqa: S603
        LOGGER.debug("Database restored from %s", snapshot_path)

    LOGGER.info("Snapshot restored from %s", snapshot_path)


def create_backup(strategy: BackupStrategy) -> bool:
    """Create a backup given the provided strategy, dealing
    with any offsite file transfer and desired retention limits.

    Arguments:
        strategy: The `BackupStrategy` config.

    Returns:
        bool: Whether the backup was successful.

    """

    snapshot_name = f"datalab-snapshot-{datetime.datetime.now(tz=datetime.timezone.utc).strftime('%Y-%m-%d-%H-%M-%S')}.tar.gz"

    if strategy.hostname is None:
        snapshot_path = strategy.location / snapshot_name

        if not strategy.location.is_dir():
            strategy.location.mkdir(parents=True, exist_ok=True)

        take_snapshot(snapshot_path)

        existing_snapshots = [
            str(s) for s in strategy.location.iterdir() if s.name.startswith("datalab-snapshot-")
        ]

        retention = strategy.retention or 100
        if len(existing_snapshots) > retention:
            LOGGER.info(
                "Cleaning up old snapshots: found %s, retention set to %s",
                len(existing_snapshots),
                strategy.retention,
            )
            # Sort into reverse order then remove from the end of the list
            sorted_snapshots = sorted(existing_snapshots, reverse=True)
            for _ in range(len(sorted_snapshots) - retention):
                snapshot_to_delete = sorted_snapshots.pop()
                LOGGER.debug("Cleaning up snapshot %s", snapshot_to_delete)
                (strategy.location / snapshot_to_delete).unlink()
    else:
        raise NotImplementedError(
            "Direct remote backup functionality has been removed and superseded."
        )

    return True
