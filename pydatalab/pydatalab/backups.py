import datetime
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from pydatalab.config import CONFIG, BackupHealth, BackupHealthCheck, BackupStrategy
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
    with tarfile.open(snapshot_path, mode=mode) as tar:
        for file in Path(CONFIG.FILE_DIRECTORY).iterdir():
            tar.add(file, arcname=Path("files") / file.relative_to(CONFIG.FILE_DIRECTORY))

        LOGGER.debug("Snapshot of %s created.", CONFIG.FILE_DIRECTORY)

        # Take a database dump and add it to the tar file
        LOGGER.debug("Taking dump of database %s", CONFIG.MONGO_URI)

        # Check that mongodump is available
        subprocess.check_output(["mongodump", "--version"])

        with tempfile.TemporaryDirectory() as temp_dir:
            command = ["mongodump", CONFIG.MONGO_URI, "--out", str(Path(temp_dir).resolve())]
            subprocess.check_output(command)

            for file in Path(temp_dir).iterdir():
                tar.add(file, arcname=Path("mongodb"))

        LOGGER.debug("Dump of database %s created.", CONFIG.MONGO_URI)

        LOGGER.debug("Dumping server config.")
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(tmp_config := Path(temp_dir) / "config.json", "w") as f:
                data = CONFIG.json(indent=2, skip_defaults=True)
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

    with tarfile.open(snapshot_path, mode=mode) as tar:
        LOGGER.debug("Restoring files from %s", snapshot_path)
        files = [m for m in tar.getmembers() if m.name.startswith("files/")]
        tar.extractall(path=CONFIG.FILE_DIRECTORY, members=files)
        LOGGER.debug("Files restored from %s", snapshot_path)

        LOGGER.debug("Restoring database from %s", snapshot_path)
        with tempfile.TemporaryDirectory() as temp_dir:
            database = [m for m in tar.getmembers() if m.name.startswith("mongodb/")]
            tar.extractall(path=temp_dir, members=database)
            command = ["mongorestore", CONFIG.MONGO_URI, "--drop", str(Path(temp_dir) / "mongodb")]
            subprocess.check_output(command)
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

    snapshot_name = f"{strategy.backup_filename_prefix}-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.tar.gz"

    if strategy.hostname is None:
        snapshot_path = strategy.location / snapshot_name

        if not strategy.location.is_dir():
            strategy.location.mkdir(parents=True, exist_ok=True)

        take_snapshot(snapshot_path)

        existing_snapshots = [
            str(s)
            for s in strategy.location.iterdir()
            if s.name.startswith(strategy.backup_filename_prefix)
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
        from paramiko.client import SSHClient
        from paramiko.config import SSHConfig

        ssh_config_path = Path.home() / ".ssh" / "config"
        ssh_cfg: dict[str, Any] = {}
        if ssh_config_path.exists():
            _ssh_cfg = SSHConfig.from_path(str(ssh_config_path.resolve()))
            ssh_cfg = dict(_ssh_cfg.lookup(strategy.hostname))

        client = SSHClient()
        client.load_system_host_keys()
        client.connect(strategy.hostname, username=ssh_cfg.get("user", None))

        sftp = client.open_sftp()
        try:
            sftp.chdir(path=str(strategy.location))
        except OSError:
            sftp.mkdir(path=str(strategy.location))
            sftp.chdir(path=str(strategy.location))

        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_path = Path(tmp_dir) / snapshot_name

            take_snapshot(snapshot_path)

            # Delete the oldest snapshots
            if strategy.retention is not None:
                existing_snapshots = [
                    s
                    for s in sftp.listdir(str(strategy.location))
                    if s.startswith(strategy.backup_filename_prefix)
                ]
                if len(existing_snapshots) > strategy.retention:
                    # Sort into reverse order then remove from the end of the list
                    sorted_snapshots = sorted(existing_snapshots, reverse=True)
                    for _ in range(len(sorted_snapshots) - strategy.retention):
                        sftp.remove(str(strategy.location / sorted_snapshots.pop()))

            sftp.put(snapshot_path, str(strategy.location / snapshot_name), confirm=True)

    return True


def backup_healthcheck(strategy: BackupStrategy) -> BackupHealthCheck:
    """Check the health of the backup strategy.

    Loop over the location where backups have been written and assess
    their health and the health of the disk.

    Assumes any folders gz files in the backup directory are backups for
    the given strategy.

    Returns:
        A dictionary used to create the backup healthcheck response.

    """

    backup_files = strategy.location.glob(f"{strategy.backup_filename_prefix}-*.gz")
    if not backup_files:
        raise RuntimeError(f"No backups found with strategy: {strategy}")

    backups: list[BackupHealth] = []
    for file in backup_files:
        backup_timestamp = datetime.datetime.strptime(
            file.name.split(strategy.backup_filename_prefix + "-")[1], "%Y-%m-%d-%H-%M-%S"
        )
        backup_health = BackupHealth(
            location=str(file.absolute()),
            size_gb=file.stat().st_size / 1e9,
            timestamp=backup_timestamp,
        )

        backups.append(backup_health)

    return BackupHealthCheck(
        status="success",
        message=f"Found {len(backups)} backups.",
        backups=backups,
    )
