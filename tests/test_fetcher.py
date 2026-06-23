import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, "..")
from fetcher import _clean_html, _parse_date, fetch_feed, RSS_SOURCES


class TestCleanHtml(unittest.TestCase):
    def test_strips_tags(self):
        self.assertEqual(_clean_html("<p>Merhaba</p>"), "Merhaba")

    def test_strips_nested_tags(self):
        self.assertEqual(_clean_html("<b><i>Bold</i></b>"), "Bold")

    def test_no_tags(self):
        self.assertEqual(_clean_html("Düz metin"), "Düz metin")

    def test_empty_string(self):
        self.assertEqual(_clean_html(""), "")

    def test_strips_whitespace(self):
        self.assertEqual(_clean_html("  <span> test </span>  "), "test")


class TestRssSources(unittest.TestCase):
    def test_all_sources_have_urls(self):
        self.assertGreater(len(RSS_SOURCES), 0)
        for name, url in RSS_SOURCES.items():
            with self.subTest(name=name):
                self.assertTrue(url.startswith("http"), f"{name} URL geçersiz: {url}")

    def test_known_sources_present(self):
        for expected in ("NTV", "Sabah", "Hürriyet"):
            self.assertIn(expected, RSS_SOURCES)


class TestFetchFeed(unittest.TestCase):
    @patch("fetcher.feedparser.parse")
    @patch("fetcher.requests.get")
    def test_returns_articles_on_success(self, mock_get, mock_parse):
        mock_get.return_value = MagicMock(content=b"<rss/>", status_code=200)
        mock_get.return_value.raise_for_status = MagicMock()

        entry = MagicMock()
        entry.get.side_effect = lambda k, default="": {
            "title":   "Haber Başlığı",
            "summary": "Özet metni",
            "link":    "https://example.com/haber",
        }.get(k, default)
        entry.published_parsed = None
        entry.updated_parsed   = None

        mock_parse.return_value = MagicMock(entries=[entry])

        articles = fetch_feed("TestKaynak", "https://example.com/rss")
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["source"], "TestKaynak")
        self.assertEqual(articles[0]["title"],  "Haber Başlığı")

    @patch("fetcher.requests.get", side_effect=Exception("Bağlantı hatası"))
    def test_returns_empty_on_error(self, _):
        articles = fetch_feed("TestKaynak", "https://example.com/rss")
        self.assertEqual(articles, [])

    @patch("fetcher.feedparser.parse")
    @patch("fetcher.requests.get")
    def test_skips_entries_without_title(self, mock_get, mock_parse):
        mock_get.return_value = MagicMock(content=b"<rss/>")
        mock_get.return_value.raise_for_status = MagicMock()

        entry = MagicMock()
        entry.get.side_effect = lambda k, default="": default  # title boş

        mock_parse.return_value = MagicMock(entries=[entry])
        articles = fetch_feed("TestKaynak", "https://example.com/rss")
        self.assertEqual(articles, [])


if __name__ == "__main__":
    unittest.main()
