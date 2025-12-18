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
            executors = {"default": ThreadPoolExecutor(10)}
            job_defaults = {"coalesce": False, "max_instances": 3}

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
        """Add a job to the scheduler or run it in a thread if APScheduler not available."""
        if self._scheduler:
            return self._scheduler.add_job(func=func, args=args, id=job_id, replace_existing=True)
        else:
            import threading

            thread = threading.Thread(target=func, args=args)
            thread.daemon = True
            thread.start()
            return None

    def shutdown(self):
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()


export_scheduler = ExportScheduler()
