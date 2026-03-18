import queue
import threading
from collections import defaultdict

from app.fetcher import fetch_url
from app.parser import parse_html, term_frequencies
from app.storage import Storage
from app.utils import normalize_url


class Crawler:
    def __init__(self, storage: Storage, worker_count: int = 4, max_queue_size: int = 100):
        self.storage = storage
        self.worker_count = worker_count
        self.max_queue_size = max_queue_size

        self.task_queue = queue.Queue(maxsize=max_queue_size)
        self.active_workers = 0
        self.active_workers_lock = threading.Lock()

        self.visited_by_job = defaultdict(set)
        self.visited_lock = threading.Lock()

        self.stop_event = threading.Event()
        self.threads = []

    def start_indexing(self, origin_url: str, max_depth: int) -> int:
        normalized_origin = normalize_url(origin_url, origin_url)
        if not normalized_origin:
            raise ValueError("Invalid origin URL")

        job_id = self.storage.create_job(normalized_origin, max_depth)
        self.storage.add_to_frontier(job_id, normalized_origin, 0)
        self.storage.add_discovery(job_id, normalized_origin, normalized_origin, 0)

        with self.visited_lock:
            self.visited_by_job[job_id].add(normalized_origin)

        self.task_queue.put((job_id, normalized_origin, normalized_origin, 0))

        self.stop_event.clear()
        self._start_workers()

        return job_id

    def _start_workers(self) -> None:
        self.threads = []
        for _ in range(self.worker_count):
            thread = threading.Thread(target=self._worker_loop, daemon=True)
            thread.start()
            self.threads.append(thread)

    def _worker_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                job_id, url, origin_url, depth = self.task_queue.get(timeout=1)
            except queue.Empty:
                continue

            with self.active_workers_lock:
                self.active_workers += 1

            try:
                self._process_url(job_id, url, origin_url, depth)
            finally:
                with self.active_workers_lock:
                    self.active_workers -= 1
                self.task_queue.task_done()

    def _process_url(self, job_id: int, url: str, origin_url: str, depth: int) -> None:
        fetch_result = fetch_url(url)

        if not fetch_result["success"]:
            return

        parsed = parse_html(url, fetch_result["html"])
        title = parsed["title"]
        body_text = parsed["body_text"]
        links = parsed["links"]

        self.storage.save_page(
            url=url,
            normalized_url=url,
            title=title,
            body_text=body_text,
            status_code=fetch_result["status_code"] or 0,
        )

        full_text = f"{title} {body_text}".strip()
        self.storage.save_terms(url, term_frequencies(full_text))

        next_depth = depth + 1

        job_row = self._get_job(job_id)
        if next_depth > job_row["max_depth"]:
            return

        for discovered_url in links:
            normalized = normalize_url(url, discovered_url)
            if not normalized:
                continue

            should_add = False
            with self.visited_lock:
                if normalized not in self.visited_by_job[job_id]:
                    self.visited_by_job[job_id].add(normalized)
                    should_add = True

            if not should_add:
                continue

            inserted = self.storage.add_to_frontier(job_id, normalized, next_depth)
            self.storage.add_discovery(job_id, normalized, origin_url, next_depth)

            if inserted:
                self.task_queue.put((job_id, normalized, origin_url, next_depth))

    def _get_job(self, job_id: int):
        conn = self.storage._get_connection()
        row = conn.execute(
            "SELECT job_id, origin_url, max_depth, status FROM crawl_jobs WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        return row

    def wait_until_done(self) -> None:
        self.task_queue.join()

    def get_runtime_status(self) -> dict:
        with self.active_workers_lock:
            active_workers = self.active_workers

        return {
            "queue_size": self.task_queue.qsize(),
            "max_queue_size": self.max_queue_size,
            "active_workers": active_workers,
            "worker_count": self.worker_count,
            "back_pressure_active": self.task_queue.qsize() >= self.max_queue_size,
        }

    def stop(self) -> None:
        self.stop_event.set()
        for thread in self.threads:
            thread.join(timeout=1)