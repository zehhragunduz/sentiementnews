import os
import sys
import tempfile
import unittest

sys.path.insert(0, "..")
from visualizer import Visualizer


def _sample_articles() -> list:
    return [
        {"source": "NTV",    "compound":  0.7,  "sentiment_label": "Pozitif"},
        {"source": "NTV",    "compound":  0.3,  "sentiment_label": "Pozitif"},
        {"source": "Sabah",  "compound": -0.6,  "sentiment_label": "Negatif"},
        {"source": "Sabah",  "compound":  0.0,  "sentiment_label": "Nötr"},
        {"source": "Milliyet","compound": -0.1, "sentiment_label": "Negatif"},
        {"source": "NTV",    "compound":  0.05, "sentiment_label": "Pozitif"},
    ]


class TestVisualizerOutputFiles(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.viz = Visualizer(output_dir=self.tmpdir)
        self.articles = _sample_articles()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_distribution_creates_file(self):
        path = self.viz.plot_sentiment_distribution(self.articles)
        self.assertTrue(os.path.isfile(path))
        self.assertGreater(os.path.getsize(path), 0)

    def test_by_source_creates_file(self):
        path = self.viz.plot_sentiment_by_source(self.articles)
        self.assertTrue(os.path.isfile(path))

    def test_histogram_creates_file(self):
        path = self.viz.plot_compound_histogram(self.articles)
        self.assertTrue(os.path.isfile(path))

    def test_avg_compound_creates_file(self):
        path = self.viz.plot_avg_compound_by_source(self.articles)
        self.assertTrue(os.path.isfile(path))

    def test_generate_all_returns_four_paths(self):
        paths = self.viz.generate_all(self.articles)
        self.assertEqual(len(paths), 4)
        for p in paths:
            self.assertTrue(os.path.isfile(p))

    def test_generate_all_empty_list(self):
        # Boş liste geçilince bile hata fırlatmamalı
        paths = self.viz.generate_all([])
        # Histogram ve avg_compound boş listede "" döner; en az dağılım grafiği kalır
        self.assertIsInstance(paths, list)


if __name__ == "__main__":
    unittest.main()
