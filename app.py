"""
SentimentNews — Streamlit Arayüzü
Çalıştırmak için: streamlit run app.py
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from fetcher import fetch_all, RSS_SOURCES
from analyzer import SentimentAnalyzer
from storage import Storage
from visualizer import Visualizer
from report import ReportGenerator

# ──────────────────────────────────────────────
# Sayfa ayarları
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="SentimentNews",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp {
    zoom: 2.0;
}
.block-container {
    padding-top: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 100% !important;
}
[data-testid="stSidebar"] { background-color: #1a252f; }
[data-testid="stSidebar"] * { color: #ecf0f1 !important; }
[data-testid="stSidebar"] .stCheckbox label { color: #ecf0f1 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #3498db !important; }
.stMetric label { font-size: 0.9rem !important; }
.stMetric [data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700; }
.big-title { font-size: 2.4rem; font-weight: 800; color: #1a252f; margin-bottom: 0; }
.sub-title { color: #7f8c8d; font-size: 1.05rem; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────
for key, default in [
    ("analyzed", []),
    ("stats", {}),
    ("chart_paths", []),
    ("txt_path", ""),
    ("html_path", ""),
    ("run_done", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ──────────────────────────────────────────────
# Kenar çubuğu
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📰 SentimentNews")
    st.markdown("---")

    st.markdown("### Haber Kaynakları")
    selected = {name: st.checkbox(name, value=True) for name in RSS_SOURCES}

    st.markdown("---")
    st.markdown("### Seçenekler")
    use_translate = st.toggle("Çeviri kullan (önerilen)", value=True)
    make_charts   = st.toggle("Grafik üret", value=True)

    st.markdown("---")
    st.markdown("### Veritabanı")
    db_path = st.text_input("Dosya yolu", value="sentimentnews.db", label_visibility="collapsed")
    st.caption(f"📂 `{db_path}`")

# ──────────────────────────────────────────────
# Başlık
# ──────────────────────────────────────────────
st.markdown('<p class="big-title">📰 SentimentNews</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Türkçe Haber Duygu Analizi — VADER + Google Translate</p>',
            unsafe_allow_html=True)

tab_analyze, tab_db, tab_about = st.tabs(["🔍 Analiz Çalıştır", "🗄️ Veritabanı", "ℹ️ Hakkında"])

# ══════════════════════════════════════════════
# TAB 1 — ANALİZ
# ══════════════════════════════════════════════
with tab_analyze:
    active_sources = {k: v for k, v in RSS_SOURCES.items() if selected.get(k)}

    col_btn1, col_btn2, col_btn3 = st.columns([2, 1.5, 1.5])
    with col_btn1:
        start = st.button(
            "🔍 Analizi Başlat",
            type="primary",
            use_container_width=True,
            disabled=not active_sources,
        )
    with col_btn2:
        clear_results = st.button("🗑️ Sonuçları Temizle", use_container_width=True)

    if not active_sources:
        st.warning("Lütfen kenar çubuğundan en az bir kaynak seçin.")

    if clear_results:
        for key in ("analyzed", "stats", "chart_paths", "txt_path", "html_path", "run_done"):
            st.session_state[key] = [] if key in ("analyzed", "chart_paths") else ({} if key == "stats" else ("" if key not in ("run_done",) else False))
        st.rerun()

    # ── Analiz ──────────────────────────────
    if start and active_sources:
        storage = Storage(db_path=db_path)

        with st.status("⏳ Analiz yapılıyor...", expanded=True) as status:

            st.write(f"📡 **{len(active_sources)} kaynaktan** haberler çekiliyor…")
            articles = fetch_all(sources=active_sources)

            if not articles:
                status.update(label="Haber alınamadı!", state="error")
                st.error("Hiç haber alınamadı. İnternet bağlantısını kontrol edin.")
                st.stop()

            st.write(f"✅ **{len(articles)} haber** alındı")

            st.write("🧠 Duygu analizi yapılıyor…")
            analyzer = SentimentAnalyzer(translate=use_translate)
            analyzed = analyzer.analyze_articles(articles)
            st.write(f"✅ **{len(analyzed)} haber** analiz edildi")

            st.write("💾 Veritabanına kaydediliyor…")
            storage.save_articles(analyzed)
            stats = storage.get_stats()
            st.write(f"✅ Kaydedildi — toplam veritabanı: **{stats['total']} haber**")

            chart_paths: list = []
            if make_charts:
                st.write("📊 Grafikler oluşturuluyor…")
                viz = Visualizer()
                chart_paths = viz.generate_all(analyzed)
                st.write(f"✅ **{len(chart_paths)} grafik** oluşturuldu")

            st.write("📄 Raporlar hazırlanıyor…")
            reporter  = ReportGenerator()
            txt_path  = reporter.generate_text_report(analyzed, stats)
            html_path = reporter.generate_html_report(analyzed, stats, chart_paths)
            st.write("✅ Raporlar hazır")

            status.update(label="✅ Analiz tamamlandı!", state="complete")

        # Sonuçları session'a kaydet
        st.session_state.analyzed    = analyzed
        st.session_state.stats       = stats
        st.session_state.chart_paths = chart_paths
        st.session_state.txt_path    = txt_path
        st.session_state.html_path   = html_path
        st.session_state.run_done    = True

    # ── Sonuçları göster ────────────────────
    if st.session_state.run_done and st.session_state.analyzed:
        stats       = st.session_state.stats
        analyzed    = st.session_state.analyzed
        chart_paths = st.session_state.chart_paths
        txt_path    = st.session_state.txt_path
        html_path   = st.session_state.html_path

        by_label = stats.get("by_label", {})
        total    = max(stats.get("total", 1), 1)
        avg      = stats.get("avg_compound", 0.0)

        st.divider()
        st.subheader("Özet İstatistikler")

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Toplam Haber",   total)
        m2.metric("Bu Sefer",       len(analyzed))
        m3.metric("Ort. Puan",      f"{avg:+.3f}")
        m4.metric("Pozitif",
                  f"{by_label.get('Pozitif', 0)}",
                  f"{by_label.get('Pozitif', 0) / total * 100:.1f}%")
        m5.metric("Negatif",
                  f"{by_label.get('Negatif', 0)}",
                  f"-{by_label.get('Negatif', 0) / total * 100:.1f}%")

        # ── Grafikler ───────────────────────
        if chart_paths:
            st.divider()
            st.subheader("Grafikler")
            row1 = st.columns(2)
            row2 = st.columns(2)
            grid = [row1[0], row1[1], row2[0], row2[1]]
            for col, path in zip(grid, chart_paths):
                if Path(path).exists():
                    col.image(path, use_container_width=True)

        # ── Haber tablosu ───────────────────
        st.divider()
        st.subheader(f"Haberler ({len(analyzed)} adet)")

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            src_opts = ["Tümü"] + sorted({a["source"] for a in analyzed})
            f_src = st.selectbox("Kaynak filtresi", src_opts, key="f_src_tab1")
        with f_col2:
            f_sent = st.selectbox("Duygu filtresi",
                                  ["Tümü", "Pozitif", "Nötr", "Negatif"], key="f_sent_tab1")

        df = pd.DataFrame(analyzed)
        if f_src  != "Tümü": df = df[df["source"] == f_src]
        if f_sent != "Tümü": df = df[df["sentiment_label"] == f_sent]

        show_cols = [c for c in ["source", "title", "compound", "sentiment_label", "published", "link"]
                     if c in df.columns]
        st.dataframe(
            df[show_cols],
            column_config={
                "source":          st.column_config.TextColumn("Kaynak",  width="small"),
                "title":           st.column_config.TextColumn("Başlık",  width="large"),
                "compound":        st.column_config.NumberColumn("Puan",  format="%.4f", width="small"),
                "sentiment_label": st.column_config.TextColumn("Duygu",   width="small"),
                "published":       st.column_config.TextColumn("Tarih",   width="medium"),
                "link":            st.column_config.LinkColumn("Bağlantı", width="small"),
            },
            use_container_width=True,
            height=420,
            hide_index=True,
        )

        # ── İndirme butonları ────────────────
        st.divider()
        st.subheader("Raporları İndir")
        d1, d2 = st.columns(2)
        with d1:
            p = Path(txt_path)
            if p.exists():
                st.download_button("📥 Metin Raporu (.txt)",
                                   p.read_text(encoding="utf-8"),
                                   file_name="sentimentnews_rapor.txt",
                                   mime="text/plain",
                                   use_container_width=True)
        with d2:
            p = Path(html_path)
            if p.exists():
                st.download_button("📥 HTML Raporu (.html)",
                                   p.read_bytes(),
                                   file_name="sentimentnews_rapor.html",
                                   mime="text/html",
                                   use_container_width=True)

# ══════════════════════════════════════════════
# TAB 2 — VERİTABANI
# ══════════════════════════════════════════════
with tab_db:
    storage = Storage(db_path=db_path)
    stats   = storage.get_stats()

    if stats["total"] == 0:
        st.info("Veritabanında henüz haber yok. 'Analiz Çalıştır' sekmesinden analiz başlatın.")
    else:
        total    = max(stats["total"], 1)
        avg      = stats["avg_compound"]
        by_label = stats.get("by_label", {})

        st.subheader("Veritabanı Özeti")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Toplam Haber", total)
        m2.metric("Ort. Puan",    f"{avg:+.3f}")
        m3.metric("Pozitif",      by_label.get("Pozitif", 0))
        m4.metric("Negatif",      by_label.get("Negatif", 0))

        # ── Kaynak tablosu ──────────────────
        st.divider()
        st.subheader("Kaynak İstatistikleri")
        src_df = pd.DataFrame(stats["by_source"]).rename(columns={
            "source": "Kaynak", "cnt": "Haber Sayısı", "avg_compound": "Ort. Puan"
        })
        st.dataframe(
            src_df,
            column_config={
                "Kaynak":       st.column_config.TextColumn(width="medium"),
                "Haber Sayısı": st.column_config.NumberColumn(width="small"),
                "Ort. Puan":    st.column_config.NumberColumn(format="%.4f", width="small"),
            },
            use_container_width=True,
            hide_index=True,
        )

        # ── Filtreli haber listesi ───────────
        st.divider()
        st.subheader("Tüm Haberler")

        fc1, fc2 = st.columns(2)
        with fc1:
            src_list = ["Tümü"] + [s["source"] for s in stats["by_source"]]
            f_src  = st.selectbox("Kaynak", src_list, key="db_src")
        with fc2:
            f_sent = st.selectbox("Duygu", ["Tümü", "Pozitif", "Nötr", "Negatif"], key="db_sent")

        all_arts = storage.get_all()
        df = pd.DataFrame(all_arts)
        if not df.empty:
            if f_src  != "Tümü": df = df[df["source"] == f_src]
            if f_sent != "Tümü": df = df[df["sentiment_label"] == f_sent]

            show_cols = [c for c in ["source", "title", "compound", "sentiment_label", "published", "link"]
                         if c in df.columns]
            st.dataframe(
                df[show_cols],
                column_config={
                    "source":          st.column_config.TextColumn("Kaynak",  width="small"),
                    "title":           st.column_config.TextColumn("Başlık",  width="large"),
                    "compound":        st.column_config.NumberColumn("Puan",  format="%.4f", width="small"),
                    "sentiment_label": st.column_config.TextColumn("Duygu",   width="small"),
                    "published":       st.column_config.TextColumn("Tarih",   width="medium"),
                    "link":            st.column_config.LinkColumn("Bağlantı", width="small"),
                },
                use_container_width=True,
                height=500,
                hide_index=True,
            )
            st.caption(f"Gösterilen: {len(df)} / Toplam: {total} haber")

        # ── Tehlikeli bölge ─────────────────
        st.divider()
        with st.expander("⚠️ Tehlikeli Bölge"):
            st.warning("Bu işlem veritabanındaki **tüm haberleri kalıcı olarak siler!**")
            confirm = st.checkbox("Silmek istediğimi onaylıyorum")
            if st.button("🗑️ Veritabanını Temizle", type="secondary", disabled=not confirm):
                storage.clear()
                st.success("Veritabanı temizlendi.")
                st.rerun()

# ══════════════════════════════════════════════
# TAB 3 — HAKKINDA
# ══════════════════════════════════════════════
with tab_about:
    st.subheader("SentimentNews Hakkında")

    col_info, col_sources = st.columns([3, 2])

    with col_info:
        st.markdown("""
**SentimentNews**, Türkçe haber kaynaklarından RSS beslemeleri çeken ve
VADER duygu analizi motoru ile her haberi otomatik olarak sınıflandıran
bir araçtır.

**Çalışma Akışı:**
1. RSS beslemeleri `feedparser` ile çekilir
2. Başlık + özet birleştirilerek `deep-translator` ile İngilizceye çevrilir
3. VADER ile `compound`, `pos`, `neg`, `neu` puanları hesaplanır
4. Sonuçlar SQLite veritabanına kaydedilir
5. `matplotlib` grafikleri ve HTML/TXT raporlar üretilir

**Duygu Etiketleri:**
| Etiket   | Koşul               |
|----------|---------------------|
| Pozitif  | compound ≥ +0.05   |
| Negatif  | compound ≤ −0.05   |
| Nötr     | −0.05 < c < +0.05  |
        """)

    with col_sources:
        st.markdown("**Desteklenen Kaynaklar:**")
        for name, url in RSS_SOURCES.items():
            st.markdown(f"- **{name}**")

        st.markdown("---")
        st.markdown("**Bağımlılıklar:**")
        st.code("""feedparser
vaderSentiment
matplotlib
deep-translator
pandas
seaborn
requests
numpy
streamlit""", language="text")
