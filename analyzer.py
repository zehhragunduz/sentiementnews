"""
Duygu analizi modülü.

VADER İngilizce bir araç olduğundan Türkçe metinler önce İngilizceye
çevrilir (deep-translator / Google Translate).  İnternet bağlantısı
yoksa çeviri atlanır ve ham Türkçe metin VADER'a verilir; sonuçlar
daha az güvenilir olsa da sistem çalışmaya devam eder.
"""

import logging
from typing import Dict, List

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

try:
    from deep_translator import GoogleTranslator
    _TRANSLATE_AVAILABLE = True
except ImportError:
    _TRANSLATE_AVAILABLE = False
    logger.warning("deep-translator kurulu değil; çeviri devre dışı.")

_EMPTY_SCORES: Dict[str, float] = {
    "compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0
}


class SentimentAnalyzer:
    def __init__(self, translate: bool = True):
        self.vader = SentimentIntensityAnalyzer()
        self._do_translate = translate and _TRANSLATE_AVAILABLE
        self._cache: Dict[str, str] = {}

        if self._do_translate:
            self._translator = GoogleTranslator(source="tr", target="en")

    # ------------------------------------------------------------------
    # Çeviri
    # ------------------------------------------------------------------

    def translate_text(self, text: str) -> str:
        """Türkçe metni İngilizceye çevirir; hata durumunda orijinali döner."""
        if not text or not self._do_translate:
            return text

        key = text[:500]
        if key in self._cache:
            return self._cache[key]

        try:
            translated = self._translator.translate(key)
            self._cache[key] = translated
            return translated
        except Exception as exc:
            logger.debug("Çeviri başarısız (%s); orijinal metin kullanılıyor.", exc)
            return text

    # ------------------------------------------------------------------
    # Analiz
    # ------------------------------------------------------------------

    def analyze(self, text: str) -> Dict[str, float]:
        """Bir metin parçasının VADER duygu puanlarını döner."""
        if not text:
            return dict(_EMPTY_SCORES)
        return self.vader.polarity_scores(self.translate_text(text))

    def analyze_article(self, article: Dict) -> Dict:
        """Bir haber sözlüğüne duygu alanları ekleyerek döner."""
        text = f"{article.get('title', '')} {article.get('summary', '')}".strip()
        scores = self.analyze(text)
        return {
            **article,
            "compound":        round(scores["compound"], 4),
            "positive":        round(scores["pos"], 4),
            "neutral":         round(scores["neu"], 4),
            "negative":        round(scores["neg"], 4),
            "sentiment_label": self._label(scores["compound"]),
        }

    def analyze_articles(self, articles: List[Dict]) -> List[Dict]:
        """Haber listesini analiz eder, ilerlemeyi loglar."""
        results = []
        total = len(articles)
        for i, article in enumerate(articles, 1):
            results.append(self.analyze_article(article))
            if i % 20 == 0 or i == total:
                logger.info("%d/%d haber analiz edildi.", i, total)
        return results

    # ------------------------------------------------------------------
    # Yardımcı
    # ------------------------------------------------------------------

    @staticmethod
    def _label(compound: float) -> str:
        if compound >= 0.05:
            return "Pozitif"
        if compound <= -0.05:
            return "Negatif"
        return "Nötr"
