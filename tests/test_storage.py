import os
import sys
import unittest

sys.path.insert(0, "..")
from storage import Storage

_TEST_DB = "test_sentimentnews_tmp.db"


def _sample() -> list:
    return [
        {
            "source": "NTV", "title": "Pozitif Haber", "summary": "Güzel gelişme",
            "link": "https://ntv.com.tr/1", "published": "2024-06-01T10:00:00",
            "fetched_at": "2024-06-01T10:05:00",
            "compound": 0.6, "positive": 0.7, "neutral": 0.2, "negative": 0.1,
            "sentiment_label": "Pozitif",
        },
        {
            "source": "Sabah", "title": "Negatif Haber", "summary": "Kötü gelişme",
            "link": "https://sabah.com.tr/1", "published": "2024-06-01T11:00:00",
            "fetched_at": "2024-06-01T11:05:00",
            "compound": -0.5, "positive": 0.05, "neutral": 0.3, "negative": 0.65,
            "sentiment_label": "Negatif",
        },
        {
            "source": "NTV", "title": "Nötr Haber", "summary": "Sıradan gelişme",
            "link": "https://ntv.com.tr/2", "published": "2024-06-01T12:00:00",
            "fetched_at": "2024-06-01T12:05:00",
            "compound": 0.0, "positive": 0.1, "neutral": 0.8, "negative": 0.1,
            "sentiment_label": "Nötr",
        },
    ]


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.db = Storage(db_path=_TEST_DB)

    def tearDown(self):
        self.db.clear()
        if os.path.exists(_TEST_DB):
            os.remove(_TEST_DB)

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------

    def test_save_returns_correct_count(self):
        inserted = self.db.save_articles(_sample())
        self.assertEqual(inserted, 3)

    def test_duplicate_link_ignored(self):
        self.db.save_articles(_sample())
        inserted_again = self.db.save_articles(_sample())
        self.assertEqual(inserted_again, 0)

    # ------------------------------------------------------------------
    # Okuma
    # ------------------------------------------------------------------

    def test_get_all_returns_all(self):
        self.db.save_articles(_sample())
        all_articles = self.db.get_all()
        self.assertEqual(len(all_articles), 3)

    def test_get_by_source(self):
        self.db.save_articles(_sample())
        ntv = self.db.get_by_source("NTV")
        self.assertEqual(len(ntv), 2)
        self.assertTrue(all(a["source"] == "NTV" for a in ntv))

    def test_get_by_sentiment(self):
        self.db.save_articles(_sample())
        pos = self.db.get_by_sentiment("Pozitif")
        self.assertEqual(len(pos), 1)
        self.assertEqual(pos[0]["sentiment_label"], "Pozitif")

    def test_get_all_empty_db(self):
        self.assertEqual(self.db.get_all(), [])

    # ------------------------------------------------------------------
    # İstatistikler
    # ------------------------------------------------------------------

    def test_stats_total(self):
        self.db.save_articles(_sample())
        stats = self.db.get_stats()
        self.assertEqual(stats["total"], 3)

    def test_stats_by_label(self):
        self.db.save_articles(_sample())
        by_lbl = self.db.get_stats()["by_label"]
        self.assertEqual(by_lbl.get("Pozitif"), 1)
        self.assertEqual(by_lbl.get("Negatif"), 1)
        self.assertEqual(by_lbl.get("Nötr"),    1)

    def test_stats_by_source(self):
        self.db.save_articles(_sample())
        by_src = {s["source"]: s for s in self.db.get_stats()["by_source"]}
        self.assertEqual(by_src["NTV"]["cnt"],   2)
        self.assertEqual(by_src["Sabah"]["cnt"], 1)

    def test_stats_avg_compound(self):
        self.db.save_articles(_sample())
        avg = self.db.get_stats()["avg_compound"]
        self.assertAlmostEqual(avg, (0.6 + -0.5 + 0.0) / 3, places=4)

    # ------------------------------------------------------------------
    # Temizlik
    # ------------------------------------------------------------------

    def test_clear(self):
        self.db.save_articles(_sample())
        self.db.clear()
        self.assertEqual(self.db.get_all(), [])


if __name__ == "__main__":
    unittest.main()
