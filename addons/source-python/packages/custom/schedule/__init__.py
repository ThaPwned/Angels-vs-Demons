from .schedule import Scheduler as _Scheduler

from core import AutoUnload
from listeners.tick import Repeat
from listeners.tick import RepeatStatus


class Scheduler(_Scheduler, AutoUnload):
    def __init__(self, accuracy=1):
        super().__init__()

        self._accuracy = accuracy

        self._repeat = Repeat(self._tick)

    def _unload_instance(self):
        if self._repeat.status is RepeatStatus.RUNNING:
            self._repeat.stop()

    def _tick(self):
        for job in sorted((job for job in self.jobs if job.should_run)):
            self._run_job(job)

    def every(self, interval=1):
        if self._repeat.status is not RepeatStatus.RUNNING:
            self._repeat.start(self._accuracy, 0)

        return super().every(interval)
