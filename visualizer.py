"""Matplotlib tabanlı görselleştirme modülü."""

import logging
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")  # GUI olmayan ortamlarda çalışması için
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

plt.rcParams.update({
    "font.family":  "DejaVu Sans",
    "figure.dpi":   100,
    "axes.spines.top":   False,
    "axes.spines.right": False,
})

_COLORS = {
    "Pozitif": "#2ecc71",
    "Nötr":    "#95a5a6",
    "Negatif": "#e74c3c",
}
_OUTPUT_DIR = Path("reports")


class Visualizer:
    def __init__(self, output_dir: str = str(_OUTPUT_DIR)):
        self.out = Path(output_dir)
        self.out.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Bireysel grafikler
    # ------------------------------------------------------------------

    def plot_sentiment_distribution(self, articles: List[Dict]) -> str:
        """Duygu dağılımı pasta grafiği."""
        counts = {k: 0 for k in _COLORS}
        for a in articles:
            lbl = a.get("sentiment_label", "Nötr")
            if lbl in counts:
                counts[lbl] += 1

        labels = list(counts.keys())
        sizes  = list(counts.values())
        colors = [_COLORS[l] for l in labels]

        fig, ax = plt.subplots(figsize=(7, 6))
        if sum(sizes) == 0:
            ax.text(0.5, 0.5, "Veri yok", ha="center", va="center",
                    transform=ax.transAxes, fontsize=14)
        else:
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                colors=colors,
                autopct="%1.1f%%",
                explode=(0.05, 0.0, 0.05),
                startangle=140,
                shadow=True,
            )
            for at in autotexts:
                at.set_fontsize(12)
        ax.set_title("Haber Duygu Dağılımı", fontsize=15, fontweight="bold", pad=18)

        path = str(self.out / "sentiment_distribution.png")
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        logger.info("Grafik: %s", path)
        return path

    def plot_sentiment_by_source(self, articles: List[Dict]) -> str:
        """Kaynaklara göre gruplanmış çubuk grafik."""
        data: Dict[str, Dict[str, int]] = {}
        for a in articles:
            src = a.get("source", "?")
            lbl = a.get("sentiment_label", "Nötr")
            data.setdefault(src, {k: 0 for k in _COLORS})
            data[src][lbl] = data[src].get(lbl, 0) + 1

        sources = list(data.keys())
        x = np.arange(len(sources))
        w = 0.25

        fig, ax = plt.subplots(figsize=(13, 6))
        for i, lbl in enumerate(["Pozitif", "Nötr", "Negatif"]):
            vals = [data[s][lbl] for s in sources]
            ax.bar(x + (i - 1) * w, vals, w, label=lbl, color=_COLORS[lbl], alpha=0.88)

        ax.set_xticks(x)
        ax.set_xticklabels(sources, rotation=30, ha="right")
        ax.set_ylabel("Haber Sayısı", fontsize=12)
        ax.set_title("Kaynaklara Göre Duygu Dağılımı", fontsize=15, fontweight="bold")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)
        ax.set_axisbelow(True)

        path = str(self.out / "sentiment_by_source.png")
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        logger.info("Grafik: %s", path)
        return path

    def plot_compound_histogram(self, articles: List[Dict]) -> str:
        """Bileşik puan histogramı."""
        scores = [a["compound"] for a in articles if a.get("compound") is not None]
        if not scores:
            return ""

        fig, ax = plt.subplots(figsize=(10, 5))
        n, bins, patches = ax.hist(scores, bins=30, edgecolor="white", linewidth=0.4)

        for patch, left in zip(patches, bins):
            if left < -0.05:
                patch.set_facecolor(_COLORS["Negatif"])
            elif left >= 0.05:
                patch.set_facecolor(_COLORS["Pozitif"])
            else:
                patch.set_facecolor(_COLORS["Nötr"])

        ax.axvline( 0.05, color="#27ae60", ls="--", lw=1.2, label="Pozitif eşik (0.05)")
        ax.axvline(-0.05, color="#c0392b", ls="--", lw=1.2, label="Negatif eşik (−0.05)")
        ax.set_xlabel("Bileşik Puan", fontsize=12)
        ax.set_ylabel("Haber Sayısı", fontsize=12)
        ax.set_title("Duygu Puanı Histogramı", fontsize=15, fontweight="bold")
        ax.legend()
        ax.grid(alpha=0.3)
        ax.set_axisbelow(True)

        path = str(self.out / "compound_histogram.png")
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        logger.info("Grafik: %s", path)
        return path

    def plot_avg_compound_by_source(self, articles: List[Dict]) -> str:
        """Kaynak başına ortalama bileşik puan (yatay çubuk)."""
        buckets: Dict[str, List[float]] = {}
        for a in articles:
            src = a.get("source", "?")
            c = a.get("compound")
            if c is not None:
                buckets.setdefault(src, []).append(c)

        if not buckets:
            return ""

        src_names = list(buckets.keys())
        avgs = [float(np.mean(buckets[s])) for s in src_names]
        colors = [_COLORS["Pozitif"] if v >= 0 else _COLORS["Negatif"] for v in avgs]

        order = sorted(range(len(avgs)), key=lambda i: avgs[i])
        src_names = [src_names[i] for i in order]
        avgs      = [avgs[i] for i in order]
        colors    = [colors[i] for i in order]

        fig, ax = plt.subplots(figsize=(10, max(4, len(src_names) * 0.6 + 1)))
        bars = ax.barh(src_names, avgs, color=colors, alpha=0.85)
        ax.axvline(0, color="black", lw=0.8)

        for bar, val in zip(bars, avgs):
            offset = 0.003 if val >= 0 else -0.003
            ax.text(
                val + offset, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center",
                ha="left" if val >= 0 else "right", fontsize=9,
            )

        ax.set_xlabel("Ortalama Bileşik Puan", fontsize=12)
        ax.set_title("Kaynak Başına Ortalama Duygu Puanı", fontsize=15, fontweight="bold")
        ax.grid(axis="x", alpha=0.3)
        ax.set_axisbelow(True)

        path = str(self.out / "avg_compound_by_source.png")
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        logger.info("Grafik: %s", path)
        return path

    # ------------------------------------------------------------------
    # Toplu üretim
    # ------------------------------------------------------------------

    def generate_all(self, articles: List[Dict]) -> List[str]:
        """Tüm grafikleri üretir, dosya yollarını liste olarak döner."""
        paths = [
            self.plot_sentiment_distribution(articles),
            self.plot_sentiment_by_source(articles),
            self.plot_compound_histogram(articles),
            self.plot_avg_compound_by_source(articles),
        ]
        return [p for p in paths if p]
