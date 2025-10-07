from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler


class ExportScheduler:
    _instance = None
    _scheduler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init_scheduler(self):
        if self._scheduler is None:
            jobstores = {"default": MemoryJobStore()}
            # TODO: Make max_workers configurable via settings
            executors = {"default": ThreadPoolExecutor(1)}
            # max_instances: max concurrent instances of the same job
            job_defaults = {"coalesce": False, "max_instances": 1}

            self._scheduler = BackgroundScheduler(
                jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone="UTC"
            )
            self._scheduler.start()
        return self._scheduler

    def get_scheduler(self):
        if self._scheduler is None:
            self.init_scheduler()
        return self._scheduler

    def add_job(self, func, args, job_id=None):
        """Add a job to the scheduler."""
        scheduler = self.get_scheduler()
        if not scheduler:
            raise RuntimeError("Failed to initialize scheduler")
        return scheduler.add_job(func=func, args=args, id=job_id, replace_existing=True)

    def shutdown(self):
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()


export_scheduler = ExportScheduler()
