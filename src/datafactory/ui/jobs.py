"""In-memory background runs of the pipeline (one at a time per dataset)."""

import logging
import threading
import uuid
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from datafactory.core.errors import DataFactoryError
from datafactory.pipeline.runner import RunResult, Stage

RunFn = Callable[[str, Stage | None, str | None, bool, datetime], RunResult]
MAX_JOBS = 100


class JobStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class DatasetBusyError(RuntimeError):
    def __init__(self, job_id: str) -> None:
        super().__init__(f"dataset already running in job {job_id}")
        self.job_id = job_id


@dataclass
class Job:
    id: str
    slug: str
    stage: Stage | None
    batch_id: str | None
    release: bool
    started_at: datetime
    now: datetime
    status: JobStatus = JobStatus.RUNNING
    finished_at: datetime | None = None
    result: RunResult | None = None
    error: str | None = None
    logs: list[str] = field(default_factory=list)
    done: threading.Event = field(default_factory=threading.Event, repr=False)


class _ThreadLogHandler(logging.Handler):
    def __init__(self, job: Job, thread_id: int) -> None:
        super().__init__(logging.INFO)
        self.job = job
        self.thread_id = thread_id
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        if record.thread == self.thread_id:
            self.job.logs.append(self.format(record))


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


class JobManager:
    """In-memory runs. ``now`` is injected for deterministic tests."""

    def __init__(
        self,
        run_fn: RunFn,
        *,
        now: Callable[[], datetime] = _utcnow,
        make_id: Callable[[], str] | None = None,
    ) -> None:
        self._run_fn = run_fn
        self._now = now
        self._make_id = make_id or (lambda: uuid.uuid4().hex[:12])
        self._jobs: OrderedDict[str, Job] = OrderedDict()
        self._lock = threading.Lock()

    def start(self, slug: str, stage: Stage | None, batch_id: str | None, release: bool) -> Job:
        job = Job(
            id=self._make_id(),
            slug=slug,
            stage=stage,
            batch_id=batch_id,
            release=release,
            started_at=self._now(),
            now=self._now(),
        )
        with self._lock:
            busy = next(
                (j for j in self._jobs.values() if j.slug == slug and not j.done.is_set()), None
            )
            if busy:
                raise DatasetBusyError(busy.id)
            self._jobs[job.id] = job
            self._evict_finished()
        threading.Thread(target=self._execute, args=(job,), daemon=True).start()
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self, slug: str | None = None) -> list[Job]:
        with self._lock:  # _execute evicts finished jobs; iterate a snapshot
            snapshot = list(reversed(self._jobs.values()))
        return [j for j in snapshot if slug is None or j.slug == slug]

    def _execute(self, job: Job) -> None:
        handler = _ThreadLogHandler(job, threading.get_ident())
        root = logging.getLogger()
        root.addHandler(handler)
        try:
            job.result = self._run_fn(job.slug, job.stage, job.batch_id, job.release, job.now)
            job.status = JobStatus.SUCCEEDED
        except DataFactoryError as exc:
            job.error = str(exc)
            job.status = JobStatus.FAILED
        except Exception as exc:  # surface unexpected bugs in the UI instead of a dead thread
            logging.getLogger(__name__).exception("job %s crashed", job.id)
            job.error = f"unexpected error: {exc!r}"
            job.status = JobStatus.FAILED
        finally:
            root.removeHandler(handler)
            job.finished_at = self._now()
            job.done.set()
            with self._lock:
                self._evict_finished()

    def _evict_finished(self) -> None:
        """Drop finished jobs oldest-first to bound memory. Running jobs are never evicted:
        if every slot is busy the cap is exceeded rather than dropping a busy guard."""
        for key, old in list(self._jobs.items()):
            if len(self._jobs) <= MAX_JOBS:
                break
            if old.done.is_set():
                del self._jobs[key]
