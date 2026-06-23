import sys
import unittest

sys.path.insert(0, "..")
from analyzer import SentimentAnalyzer


class TestSentimentLabel(unittest.TestCase):
    def test_positive_label(self):
        self.assertEqual(SentimentAnalyzer._label(0.5),  "Pozitif")
        self.assertEqual(SentimentAnalyzer._label(0.05), "Pozitif")

    def test_negative_label(self):
        self.assertEqual(SentimentAnalyzer._label(-0.5),  "Negatif")
        self.assertEqual(SentimentAnalyzer._label(-0.05), "Negatif")

    def test_neutral_label(self):
        self.assertEqual(SentimentAnalyzer._label(0.0),   "Nötr")
        self.assertEqual(SentimentAnalyzer._label(0.04),  "Nötr")
        self.assertEqual(SentimentAnalyzer._label(-0.04), "Nötr")


class TestAnalyzeText(unittest.TestCase):
    """Çeviri kapalı; İngilizce metin doğrudan VADER'a verilir."""

    def setUp(self):
        self.analyzer = SentimentAnalyzer(translate=False)

    def test_positive_text(self):
        scores = self.analyzer.analyze("This is wonderful, excellent, and amazing!")
        self.assertGreater(scores["compound"], 0.05)

    def test_negative_text(self):
        scores = self.analyzer.analyze("This is terrible, horrible, and devastating.")
        self.assertLess(scores["compound"], -0.05)

    def test_empty_text(self):
        scores = self.analyzer.analyze("")
        self.assertEqual(scores["compound"], 0.0)
        self.assertEqual(scores["neu"],      1.0)

    def test_score_keys_present(self):
        scores = self.analyzer.analyze("Hello world")
        for key in ("compound", "pos", "neu", "neg"):
            self.assertIn(key, scores)


class TestAnalyzeArticle(unittest.TestCase):
    def setUp(self):
        self.analyzer = SentimentAnalyzer(translate=False)

    def test_adds_sentiment_fields(self):
        article = {"title": "Great victory", "summary": "Team wins the championship"}
        result = self.analyzer.analyze_article(article)
        for field in ("compound", "positive", "neutral", "negative", "sentiment_label"):
            self.assertIn(field, result)

    def test_preserves_original_fields(self):
        article = {"title": "Test", "summary": "Summary", "source": "NTV", "link": "https://x.com"}
        result = self.analyzer.analyze_article(article)
        self.assertEqual(result["source"], "NTV")
        self.assertEqual(result["link"],   "https://x.com")

    def test_missing_fields_do_not_raise(self):
        result = self.analyzer.analyze_article({})
        self.assertIn("sentiment_label", result)


class TestAnalyzeArticles(unittest.TestCase):
    def setUp(self):
        self.analyzer = SentimentAnalyzer(translate=False)

    def test_returns_same_length(self):
        articles = [
            {"title": "Good news today", "summary": "Everything is fine"},
            {"title": "Bad disaster",    "summary": "Terrible events"},
        ]
        results = self.analyzer.analyze_articles(articles)
        self.assertEqual(len(results), len(articles))

    def test_empty_list(self):
        self.assertEqual(self.analyzer.analyze_articles([]), [])


if __name__ == "__main__":
    unittest.main()
