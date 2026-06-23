"""Metin ve HTML rapor üretici."""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

_OUTPUT_DIR = Path("reports")


class ReportGenerator:
    def __init__(self, output_dir: str = str(_OUTPUT_DIR)):
        self.out = Path(output_dir)
        self.out.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Metin raporu
    # ------------------------------------------------------------------

    def generate_text_report(self, articles: List[Dict], stats: Dict) -> str:
        total = stats.get("total", 0)
        avg   = stats.get("avg_compound", 0.0)

        def pct(count: int) -> str:
            return f"{count / total * 100:.1f}%" if total else "0.0%"

        lines = [
            "=" * 62,
            "        SENTİMENTNEWS — DUYGU ANALİZİ RAPORU",
            f"        {datetime.now().strftime('%d.%m.%Y  %H:%M:%S')}",
            "=" * 62,
            "",
            f"  Toplam haber          : {total}",
            f"  Ortalama duygu puanı  : {avg:+.4f}",
            "",
            "  Duygu dağılımı:",
        ]
        for lbl, cnt in stats.get("by_label", {}).items():
            bar = "█" * (cnt * 20 // max(total, 1))
            lines.append(f"    {lbl:10s} {cnt:4d} ({pct(cnt)})  {bar}")

        lines += ["", "  Kaynak istatistikleri:"]
        for src in stats.get("by_source", []):
            lines.append(
                f"    {src['source']:15s}  {src['cnt']:3d} haber  "
                f"ort. puan: {src['avg_compound']:+.3f}"
            )

        top_pos = sorted(articles, key=lambda a: a.get("compound", 0), reverse=True)[:5]
        top_neg = sorted(articles, key=lambda a: a.get("compound", 0))[:5]

        lines += ["", "  En pozitif 5 haber:"]
        for a in top_pos:
            lines.append(f"    [{a.get('source', '?'):10s}] {a.get('title', '')[:65]}")
            lines.append(f"              puan: {a.get('compound', 0):+.4f}")

        lines += ["", "  En negatif 5 haber:"]
        for a in top_neg:
            lines.append(f"    [{a.get('source', '?'):10s}] {a.get('title', '')[:65]}")
            lines.append(f"              puan: {a.get('compound', 0):+.4f}")

        lines += ["", "=" * 62, ""]

        path = self.out / "report.txt"
        path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Metin raporu: %s", path)
        return str(path)

    # ------------------------------------------------------------------
    # HTML raporu
    # ------------------------------------------------------------------

    def generate_html_report(
        self, articles: List[Dict], stats: Dict, chart_paths: List[str]
    ) -> str:
        total     = stats.get("total", 1)
        avg       = stats.get("avg_compound", 0.0)
        by_label  = stats.get("by_label", {})
        by_source = stats.get("by_source", [])

        pos_pct = by_label.get("Pozitif", 0) / total * 100
        neg_pct = by_label.get("Negatif", 0) / total * 100

        def b64_img(path: str) -> str:
            try:
                data = Path(path).read_bytes()
                return f'<img src="data:image/png;base64,{base64.b64encode(data).decode()}" class="chart">'
            except Exception:
                return ""

        charts_html = "\n".join(b64_img(p) for p in chart_paths)

        def article_table_rows(arts: List[Dict]) -> str:
            rows = []
            for a in arts:
                c = a.get("compound", 0.0)
                lbl = a.get("sentiment_label", "Nötr")
                color = {"Pozitif": "#2ecc71", "Negatif": "#e74c3c"}.get(lbl, "#95a5a6")
                link  = a.get("link", "#")
                title = (a.get("title") or "")[:90]
                rows.append(
                    f"<tr>"
                    f"<td>{a.get('source', '')}</td>"
                    f'<td><a href="{link}" target="_blank">{title}</a></td>'
                    f'<td style="color:{color};font-weight:600">{c:+.4f}</td>'
                    f'<td style="color:{color}">{lbl}</td>'
                    f"</tr>"
                )
            return "\n".join(rows)

        top_pos = sorted(articles, key=lambda a: a.get("compound", 0), reverse=True)[:5]
        top_neg = sorted(articles, key=lambda a: a.get("compound", 0))[:5]

        source_rows = "\n".join(
            f"<tr><td>{s['source']}</td><td>{s['cnt']}</td>"
            f"<td>{s['avg_compound']:+.4f}</td></tr>"
            for s in by_source
        )

        html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SentimentNews Raporu</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body  {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f0f2f5;
             color: #2c3e50; padding: 24px; }}
    h1   {{ font-size: 1.8rem; color: #1a252f; margin-bottom: 4px; }}
    h2   {{ font-size: 1.2rem; color: #34495e; margin: 28px 0 10px; }}
    .ts  {{ color: #7f8c8d; font-size: .85rem; margin-bottom: 20px; }}
    .cards {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }}
    .card  {{ flex: 1 1 160px; background: #fff; border-radius: 10px;
               padding: 18px 22px; text-align: center;
               box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
    .card .val {{ font-size: 2rem; font-weight: 700; }}
    .pos {{ color: #2ecc71; }} .neg {{ color: #e74c3c; }} .neu {{ color: #95a5a6; }}
    .chart {{ max-width: 100%; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,.1);
               display: block; margin: 12px 0; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff;
             border-radius: 8px; overflow: hidden;
             box-shadow: 0 2px 8px rgba(0,0,0,.07); }}
    th {{ background: #2980b9; color: #fff; padding: 9px 12px; text-align: left;
          font-size: .9rem; }}
    td {{ padding: 7px 12px; border-bottom: 1px solid #ecf0f1; font-size: .88rem; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover {{ background: #f7fbff; }}
    a  {{ color: #2980b9; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .section {{ background: #fff; border-radius: 10px; padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,.07); margin-bottom: 20px; }}
  </style>
</head>
<body>
  <h1>SentimentNews — Türkçe Haber Duygu Analizi</h1>
  <p class="ts">Rapor tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>

  <div class="cards">
    <div class="card"><div>Toplam Haber</div><div class="val">{total}</div></div>
    <div class="card"><div>Ort. Puan</div>
      <div class="val {'pos' if avg >= 0 else 'neg'}">{avg:+.3f}</div></div>
    <div class="card"><div>Pozitif</div>
      <div class="val pos">{pos_pct:.1f}%</div></div>
    <div class="card"><div>Negatif</div>
      <div class="val neg">{neg_pct:.1f}%</div></div>
  </div>

  <div class="section">
    <h2>Grafikler</h2>
    {charts_html if charts_html else '<p>Grafik bulunamadı.</p>'}
  </div>

  <div class="section">
    <h2>En Pozitif 5 Haber</h2>
    <table>
      <tr><th>Kaynak</th><th>Başlık</th><th>Puan</th><th>Duygu</th></tr>
      {article_table_rows(top_pos)}
    </table>
  </div>

  <div class="section">
    <h2>En Negatif 5 Haber</h2>
    <table>
      <tr><th>Kaynak</th><th>Başlık</th><th>Puan</th><th>Duygu</th></tr>
      {article_table_rows(top_neg)}
    </table>
  </div>

  <div class="section">
    <h2>Kaynak İstatistikleri</h2>
    <table>
      <tr><th>Kaynak</th><th>Haber Sayısı</th><th>Ort. Puan</th></tr>
      {source_rows}
    </table>
  </div>
</body>
</html>"""

        path = self.out / "report.html"
        path.write_text(html, encoding="utf-8")
        logger.info("HTML raporu: %s", path)
        return str(path)
