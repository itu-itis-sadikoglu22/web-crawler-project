import sqlite3
import threading
from pathlib import Path
from typing import List, Tuple


DB_PATH = Path("data/crawler.db")


class Storage:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._local = threading.local()
        self._ensure_data_dir()
        self._initialize_database()

    def _ensure_data_dir(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn"):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            self._local.conn = conn
        return self._local.conn

    def _initialize_database(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")

        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS crawl_jobs (
                job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin_url TEXT NOT NULL,
                max_depth INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS pages (
                url TEXT PRIMARY KEY,
                normalized_url TEXT NOT NULL,
                title TEXT,
                body_text TEXT,
                status_code INTEGER,
                fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS discoveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                page_url TEXT NOT NULL,
                origin_url TEXT NOT NULL,
                depth INTEGER NOT NULL,
                UNIQUE(job_id, page_url),
                FOREIGN KEY(job_id) REFERENCES crawl_jobs(job_id)
            );

            CREATE TABLE IF NOT EXISTS frontier (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                depth INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                UNIQUE(job_id, url),
                FOREIGN KEY(job_id) REFERENCES crawl_jobs(job_id)
            );

            CREATE TABLE IF NOT EXISTS inverted_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL,
                page_url TEXT NOT NULL,
                frequency INTEGER NOT NULL,
                UNIQUE(term, page_url)
            );

            CREATE INDEX IF NOT EXISTS idx_discoveries_job_id ON discoveries(job_id);
            CREATE INDEX IF NOT EXISTS idx_discoveries_page_url ON discoveries(page_url);
            CREATE INDEX IF NOT EXISTS idx_frontier_job_status ON frontier(job_id, status);
            CREATE INDEX IF NOT EXISTS idx_inverted_term ON inverted_index(term);
            """
        )

        conn.commit()
        conn.close()

    def create_job(self, origin_url: str, max_depth: int) -> int:
        conn = self._get_connection()
        cursor = conn.execute(
            """
            INSERT INTO crawl_jobs (origin_url, max_depth, status)
            VALUES (?, ?, 'active')
            """,
            (origin_url, max_depth),
        )
        conn.commit()
        return cursor.lastrowid

    def mark_job_completed(self, job_id: int) -> None:
        conn = self._get_connection()
        conn.execute(
            """
            UPDATE crawl_jobs
            SET status = 'completed'
            WHERE job_id = ?
            """,
            (job_id,),
        )
        conn.commit()

    def add_to_frontier(self, job_id: int, url: str, depth: int) -> bool:
        conn = self._get_connection()
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO frontier (job_id, url, depth, status)
            VALUES (?, ?, ?, 'pending')
            """,
            (job_id, url, depth),
        )
        conn.commit()
        return cursor.rowcount > 0

    def mark_frontier_in_progress(self, frontier_id: int) -> None:
        conn = self._get_connection()
        conn.execute(
            """
            UPDATE frontier
            SET status = 'in_progress'
            WHERE id = ?
            """,
            (frontier_id,),
        )
        conn.commit()

    def mark_frontier_done(self, frontier_id: int) -> None:
        conn = self._get_connection()
        conn.execute(
            """
            UPDATE frontier
            SET status = 'done'
            WHERE id = ?
            """,
            (frontier_id,),
        )
        conn.commit()

    def mark_frontier_failed(self, frontier_id: int) -> None:
        conn = self._get_connection()
        conn.execute(
            """
            UPDATE frontier
            SET status = 'failed'
            WHERE id = ?
            """,
            (frontier_id,),
        )
        conn.commit()

    def get_pending_frontier(self, job_id: int, limit: int = 100) -> List[sqlite3.Row]:
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT id, url, depth
            FROM frontier
            WHERE job_id = ? AND status = 'pending'
            ORDER BY id ASC
            LIMIT ?
            """,
            (job_id, limit),
        )
        return cursor.fetchall()

    def save_page(
        self,
        url: str,
        normalized_url: str,
        title: str,
        body_text: str,
        status_code: int,
    ) -> None:
        conn = self._get_connection()
        conn.execute(
            """
            INSERT INTO pages (url, normalized_url, title, body_text, status_code)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                normalized_url = excluded.normalized_url,
                title = excluded.title,
                body_text = excluded.body_text,
                status_code = excluded.status_code,
                fetched_at = CURRENT_TIMESTAMP
            """,
            (url, normalized_url, title, body_text, status_code),
        )
        conn.commit()

    def add_discovery(self, job_id: int, page_url: str, origin_url: str, depth: int) -> None:
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR IGNORE INTO discoveries (job_id, page_url, origin_url, depth)
            VALUES (?, ?, ?, ?)
            """,
            (job_id, page_url, origin_url, depth),
        )
        conn.commit()

    def save_terms(self, page_url: str, term_frequencies: List[Tuple[str, int]]) -> None:
        conn = self._get_connection()

        conn.execute("DELETE FROM inverted_index WHERE page_url = ?", (page_url,))
        conn.executemany(
            """
            INSERT INTO inverted_index (term, page_url, frequency)
            VALUES (?, ?, ?)
            """,
            [(term, page_url, freq) for term, freq in term_frequencies],
        )
        conn.commit()

    def search(self, query_terms: List[str]) -> List[sqlite3.Row]:
        if not query_terms:
            return []

        conn = self._get_connection()
        placeholders = ",".join("?" for _ in query_terms)

        cursor = conn.execute(
            f"""
            SELECT
                ii.page_url AS relevant_url,
                d.origin_url AS origin_url,
                d.depth AS depth,
                SUM(ii.frequency) AS score
            FROM inverted_index ii
            JOIN discoveries d ON d.page_url = ii.page_url
            WHERE ii.term IN ({placeholders})
            GROUP BY ii.page_url, d.origin_url, d.depth
            ORDER BY score DESC, d.depth ASC, ii.page_url ASC
            """,
            query_terms,
        )
        return cursor.fetchall()

    def get_status(self) -> dict:
        conn = self._get_connection()

        active_jobs = conn.execute(
            "SELECT COUNT(*) AS count FROM crawl_jobs WHERE status = 'active'"
        ).fetchone()["count"]

        pages_count = conn.execute(
            "SELECT COUNT(*) AS count FROM pages"
        ).fetchone()["count"]

        pending_count = conn.execute(
            "SELECT COUNT(*) AS count FROM frontier WHERE status = 'pending'"
        ).fetchone()["count"]

        in_progress_count = conn.execute(
            "SELECT COUNT(*) AS count FROM frontier WHERE status = 'in_progress'"
        ).fetchone()["count"]

        done_count = conn.execute(
            "SELECT COUNT(*) AS count FROM frontier WHERE status = 'done'"
        ).fetchone()["count"]

        failed_count = conn.execute(
            "SELECT COUNT(*) AS count FROM frontier WHERE status = 'failed'"
        ).fetchone()["count"]

        return {
            "active_jobs": active_jobs,
            "pages_indexed": pages_count,
            "pending_queue": pending_count,
            "in_progress": in_progress_count,
            "completed": done_count,
            "failed": failed_count,
        }

    def close(self) -> None:
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            del self._local.conn