import contextvars
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

from apscheduler.schedulers.background import BackgroundScheduler

from pydatalab.logger import LOGGER, request_id_var


class TaskScheduler:
    """Manages one-shot background jobs via a ThreadPoolExecutor and
    periodic jobs via APScheduler (in-memory job store only).

    One-shot jobs (block processing, exports) are submitted directly to the
    thread pool — no pickling, no MongoDB coordination, no cross-worker races.
    The tasks collection in MongoDB is the source of truth for queue state.

    Periodic jobs (e.g. stale task cleanup) use APScheduler's interval trigger
    with a MemoryJobStore. Each gunicorn worker runs its own cleanup
    independently; the cleanup logic is idempotent so this is safe.

    Cron jobs (e.g. daily stats cache) use APScheduler's cron trigger with a
    MemoryJobStore.
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
            from pydatalab.mongo import flask_mongo

            pending = flask_mongo.db.tasks.count_documents(
                {"status": {"$in": ["pending", "processing"]}}
            )
            LOGGER.info(
                "Submitting job %s to executor (queue depth: %d pending/processing tasks)",
                job_id or func.__name__,
                pending,
            )
        except Exception:
            LOGGER.info("Submitting job %s to executor", job_id or func.__name__)

        # Run the job in a copy of the current context, so that its log
        # lines carry the request ID of the request that spawned it
        ctx = contextvars.copy_context()
        return executor.submit(ctx.run, func, *args)

    def _add_scheduled_job(self, func, job_id, replace_existing=True, **trigger_args):
        scheduler = self._get_scheduler()

        @wraps(func)
        def job_with_log_context(*args, **kwargs):
            request_id_var.set(job_id)
            return func(*args, **kwargs)

        scheduler.add_job(
            func=job_with_log_context,
            id=job_id,
            replace_existing=replace_existing,
            misfire_grace_time=None,
            **trigger_args,
        )

    def add_periodic_job(self, func, job_id, hours, replace_existing=True):
        """Register a periodic job via APScheduler (MemoryJobStore)."""
        self._add_scheduled_job(
            func, job_id, replace_existing=replace_existing, trigger="interval", hours=hours
        )

    def add_cron_job(self, func, job_id, hour, minute=0, jitter=None, replace_existing=True):
        """Register a job that runs daily at a fixed UTC time via APScheduler (MemoryJobStore).

        Unlike an interval job, the schedule does not reset when the server restarts.
        As each worker registers its own copy of the job, `jitter` (in seconds) can be
        used to spread their runs out.
        """
        self._add_scheduled_job(
            func,
            job_id,
            replace_existing=replace_existing,
            trigger="cron",
            hour=hour,
            minute=minute,
            jitter=jitter,
        )

    def shutdown(self):
        if self._executor:
            self._executor.shutdown(wait=False)
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()


task_scheduler = TaskScheduler()
