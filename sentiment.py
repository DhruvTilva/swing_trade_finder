"""News RSS + VADER sentiment for symbols."""
import logging
from functools import lru_cache
from typing import List

import requests
import feedparser
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    try:
        nltk.download("vader_lexicon")
    except Exception:
        pass

_sia = SentimentIntensityAnalyzer()

def _fetch_yahoo_rss(symbol: str) -> List[str]:
    base = symbol.split(".")[0]
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={base}&region=IN&lang=en-IN"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except Exception:
        return []
    feed = feedparser.parse(r.text)
    titles = []
    for e in feed.entries[:20]:
        t = e.get("title", "")
        if t:
            titles.append(t)
    return titles

@lru_cache(maxsize=2048)
def get_sentiment_for_symbol(symbol: str) -> float:
    try:
        headlines = _fetch_yahoo_rss(symbol)
    except Exception:
        headlines = []
    if not headlines:
        return 0.0
    scores = []
    for h in headlines:
        try:
            s = _sia.polarity_scores(h)["compound"]
            scores.append(s)
        except Exception:
            continue
    if not scores:
        return 0.0
    return sum(scores) / len(scores)
