"""
SentimentNews — Türkçe Haber Duygu Analizi

Kullanım:
    python main.py                  # tam akış
    python main.py --no-translate   # çeviri olmadan
    python main.py --no-charts      # grafik üretme
    python main.py --sources NTV Sabah  # belirli kaynaklar
    python main.py --stats-only     # sadece DB istatistikleri
"""

import argparse
import logging
import sys

from fetcher   import fetch_all, RSS_SOURCES
from analyzer  import SentimentAnalyzer
from storage   import Storage
from visualizer import Visualizer
from report    import ReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="SentimentNews — Türkçe haber duygu analizi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--sources", nargs="+", metavar="KAYNAK",
        help="Kullanılacak kaynaklar (ör: NTV Sabah). Varsayılan: hepsi.",
    )
    p.add_argument(
        "--no-translate", action="store_true",
        help="Çeviriyi devre dışı bırak (VADER doğrudan Türkçeye uygulanır).",
    )
    p.add_argument(
        "--no-charts", action="store_true",
        help="Grafik dosyaları üretme.",
    )
    p.add_argument(
        "--stats-only", action="store_true",
        help="RSS çekmeden yalnızca veritabanı istatistiklerini göster.",
    )
    p.add_argument(
        "--db", default="sentimentnews.db", metavar="DOSYA",
        help="SQLite veritabanı dosya yolu.",
    )
    return p


def run(args: argparse.Namespace) -> int:
    storage = Storage(db_path=args.db)

    # Sadece istatistik modu
    if args.stats_only:
        stats = storage.get_stats()
        print(f"\nToplam haber   : {stats['total']}")
        print(f"Ort. puan      : {stats['avg_compound']:+.4f}")
        print("\nDuygu dağılımı :")
        for lbl, cnt in stats["by_label"].items():
            print(f"  {lbl:10s}: {cnt}")
        print("\nKaynak sıralaması:")
        for s in stats["by_source"]:
            print(f"  {s['source']:15s} {s['cnt']:3d} haber  ort. {s['avg_compound']:+.3f}")
        return 0

    # 1. Haberleri çek
    sources = None
    if args.sources:
        sources = {k: v for k, v in RSS_SOURCES.items() if k in args.sources}
        if not sources:
            logger.error("Geçerli kaynak bulunamadı. Mevcut kaynaklar: %s", list(RSS_SOURCES))
            return 1

    logger.info("Haberler çekiliyor...")
    articles = fetch_all(sources=sources)
    if not articles:
        logger.warning("Hiç haber alınamadı. İnternet bağlantısını kontrol edin.")
        return 1

    # 2. Duygu analizi
    logger.info("Duygu analizi yapılıyor...")
    analyzer = SentimentAnalyzer(translate=not args.no_translate)
    analyzed = analyzer.analyze_articles(articles)

    # 3. Veritabanına kaydet
    storage.save_articles(analyzed)
    stats = storage.get_stats()

    # 4. Grafikler
    chart_paths: list = []
    if not args.no_charts:
        logger.info("Grafikler oluşturuluyor...")
        viz = Visualizer()
        chart_paths = viz.generate_all(analyzed)

    # 5. Rapor
    logger.info("Rapor hazırlanıyor...")
    reporter = ReportGenerator()
    txt_path  = reporter.generate_text_report(analyzed, stats)
    html_path = reporter.generate_html_report(analyzed, stats, chart_paths)

    print(f"\n  Metin raporu : {txt_path}")
    print(f"  HTML raporu  : {html_path}")
    print(f"  Toplam haber : {stats['total']}")
    print(f"  Ort. puan    : {stats['avg_compound']:+.4f}\n")
    return 0


def main() -> None:
    parser = _build_parser()
    args   = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
