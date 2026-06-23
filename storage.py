"""SQLite tabanlı kalıcı depolama katmanı."""

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_DB = "sentimentnews.db"

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT    NOT NULL,
    title           TEXT    NOT NULL,
    summary         TEXT,
    link            TEXT    UNIQUE,
    published       TEXT,
    fetched_at      TEXT,
    compound        REAL,
    positive        REAL,
    neutral         REAL,
    negative        REAL,
    sentiment_label TEXT,
    created_at      TEXT    DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_source    ON articles(source);
CREATE INDEX IF NOT EXISTS idx_sentiment ON articles(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_published ON articles(published);
"""

_INSERT_SQL = """
INSERT OR IGNORE INTO articles
    (source, title, summary, link, published, fetched_at,
     compound, positive, neutral, negative, sentiment_label)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


class Storage:
    def __init__(self, db_path: str = DEFAULT_DB):
        self.db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    # Bağlantı / şema
    # ------------------------------------------------------------------

    @contextmanager
    def _connect(self):
        """Commit+close garantili bağlantı context manager'ı."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_CREATE_SQL)

    # ------------------------------------------------------------------
    # Yazma
    # ------------------------------------------------------------------

    def save_articles(self, articles: List[Dict]) -> int:
        """Haberleri kaydeder; yinelenenler atlanır. Eklenen satır sayısını döner."""
        inserted = 0
        with self._connect() as conn:
            for a in articles:
                try:
                    conn.execute(_INSERT_SQL, (
                        a.get("source", ""),
                        a.get("title", ""),
                        a.get("summary", ""),
                        a.get("link", ""),
                        a.get("published", ""),
                        a.get("fetched_at", datetime.now().isoformat()),
                        a.get("compound"),
                        a.get("positive"),
                        a.get("neutral"),
                        a.get("negative"),
                        a.get("sentiment_label"),
                    ))
                    inserted += conn.execute("SELECT changes()").fetchone()[0]
                except Exception as exc:
                    logger.error("Kayıt hatası: %s", exc)
        logger.info("%d yeni haber veritabanına kaydedildi.", inserted)
        return inserted

    # ------------------------------------------------------------------
    # Okuma
    # ------------------------------------------------------------------

    def get_all(self) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM articles ORDER BY published DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_by_source(self, source: str) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM articles WHERE source = ? ORDER BY published DESC",
                (source,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_by_sentiment(self, label: str) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM articles WHERE sentiment_label = ? ORDER BY compound DESC",
                (label,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> Dict:
        """Özet istatistikleri döner."""
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
            by_label = conn.execute(
                "SELECT sentiment_label, COUNT(*) as cnt FROM articles GROUP BY sentiment_label"
            ).fetchall()
            by_source = conn.execute(
                """SELECT source,
                          COUNT(*) AS cnt,
                          AVG(compound) AS avg_compound
                   FROM articles
                   GROUP BY source
                   ORDER BY cnt DESC"""
            ).fetchall()
            avg_compound = conn.execute("SELECT AVG(compound) FROM articles").fetchone()[0]

        return {
            "total":        total,
            "by_label":     {r["sentiment_label"]: r["cnt"] for r in by_label},
            "by_source":    [dict(r) for r in by_source],
            "avg_compound": avg_compound or 0.0,
        }

    # ------------------------------------------------------------------
    # Temizlik
    # ------------------------------------------------------------------

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM articles")
        logger.info("Veritabanı temizlendi.")
