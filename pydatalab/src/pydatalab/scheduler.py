from concurrent.futures import ThreadPoolExecutor

from apscheduler.schedulers.background import BackgroundScheduler

from pydatalab.logger import LOGGER


class TaskScheduler:
    """Manages one-shot background jobs via a ThreadPoolExecutor and
    periodic jobs via APScheduler (in-memory job store only).

    One-shot jobs (block processing, exports) are submitted directly to the
    thread pool — no pickling, no MongoDB coordination, no cross-worker races.
    The tasks collection in MongoDB is the source of truth for queue state.

    Periodic jobs (e.g. stale task cleanup) use APScheduler's interval trigger
    with a MemoryJobStore. Each gunicorn worker runs its own cleanup
    independently; the cleanup logic is idempotent so this is safe.
    """

    _instance = None
    _executor = None
    _scheduler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_executor(self):
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=1)
        return self._executor

    def _get_scheduler(self):
        """Get or create the APScheduler instance for periodic jobs only."""
        if self._scheduler is None:
            self._scheduler = BackgroundScheduler(timezone="UTC")
            self._scheduler.start()
        return self._scheduler

    def add_job(self, func, args, job_id=None):
        """Submit a one-shot job to the thread pool.

        Queue depth is logged on each submission by counting PENDING/PROCESSING
        tasks in MongoDB.
        """
        executor = self._get_executor()

        try:
            from pydatalab.mongo import get_database

            pending = get_database().tasks.count_documents(
                {"status": {"$in": ["pending", "processing"]}}
            )
            LOGGER.info(
                "Submitting job %s to executor (queue depth: %d pending/processing tasks)",
                job_id or func.__name__,
                pending,
            )
        except Exception:
            LOGGER.info("Submitting job %s to executor", job_id or func.__name__)

        return executor.submit(func, *args)

    def add_periodic_job(self, func, job_id, hours, replace_existing=True):
        """Register a periodic job via APScheduler (MemoryJobStore)."""
        scheduler = self._get_scheduler()
        scheduler.add_job(
            func=func,
            trigger="interval",
            id=job_id,
            hours=hours,
            replace_existing=replace_existing,
            misfire_grace_time=None,
        )

    def shutdown(self):
        if self._executor:
            self._executor.shutdown(wait=False)
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()


task_scheduler = TaskScheduler()
