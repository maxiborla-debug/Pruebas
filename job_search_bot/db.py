import sqlite3
from pathlib import Path

from .models import JobPosting

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    uid TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    url TEXT NOT NULL,
    salary TEXT,
    posted_date TEXT,
    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
    matched INTEGER DEFAULT 0,
    applied INTEGER DEFAULT 0
);
"""


class JobDB:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute(SCHEMA)
        self.conn.commit()

    def is_new(self, job: JobPosting) -> bool:
        cur = self.conn.execute("SELECT 1 FROM jobs WHERE uid = ?", (job.uid,))
        return cur.fetchone() is None

    def save(self, job: JobPosting, matched: bool) -> None:
        self.conn.execute(
            """INSERT OR IGNORE INTO jobs
               (uid, source, title, company, location, url, salary, posted_date, matched)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                job.uid,
                job.source,
                job.title,
                job.company,
                job.location,
                job.url,
                job.salary,
                job.posted_date,
                int(matched),
            ),
        )
        self.conn.commit()

    def mark_applied(self, uid: str) -> None:
        self.conn.execute("UPDATE jobs SET applied = 1 WHERE uid = ?", (uid,))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
