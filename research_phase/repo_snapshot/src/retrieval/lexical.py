"""Shared lexical normalization; contains no benchmark answers or trust labels."""
import re
import math
from collections import Counter
from functools import lru_cache
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

STOPWORDS = (set(ENGLISH_STOP_WORDS) - {'us'}) | {
    'please', 'tell', 'according', 'approximately', 'roughly', 'rounded',
    'decimal', 'places', 'place', 'value', 'give', 'does', 'did', 'was', 'were',
    'divided', 'approximate', 'based', 'reported', 'figure', 'figures',
}

@lru_cache(maxsize=8192)
def tokens(text: str) -> list[str]:
    text = re.sub(r"['\u2019]s\b", '', text.casefold())
    text = re.sub(r'\bwdi\b', 'world development indicators', text)
    text = re.sub(r'\bafghan\b', 'afghanistan', text)
    words = re.findall(r"[^\W_]+(?:[.%-][^\W_]+)*", text)
    # Modest inflection normalization, applied equally to queries and passages.
    normalized = [w[:-3]+'y' if len(w)>4 and w.endswith('ies') else
                  w[:-1] if len(w)>4 and w.endswith('s') and not w.endswith(('ss','us','is')) else w
                  for w in words if w not in STOPWORDS]
    return [w for w in normalized if w not in STOPWORDS]

@lru_cache(maxsize=2048)
def query_tokens(text: str) -> list[str]:
    # Source attribution is not the fact being asked for. Keep the entity,
    # indicator, unit and year, rather than rewarding a source-only header.
    text = re.sub(r'(?i)according to[^,?]*(?:,|$)', '', text)
    text = re.sub(r'(?i)(?:the )?world bank wdi value of', '', text)
    text = re.sub(r'(?i)in what year|what year', '', text)
    words = tokens(text)
    # "capital city" asks for the same relation as "capital".
    return [w for w in words if not (w == 'city' and 'capital' in words)]

@lru_cache(maxsize=8192)
def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', text) if s.strip()]

def content_weights(passages: list[str]) -> dict[str, float]:
    counts=Counter(w for text in passages for w in set(tokens(text)))
    return {w:1+math.log((len(passages)+1)/(n+1)) for w,n in counts.items()}

def sentence_score(query: str, sentence: str, weights=None) -> tuple[float, float, float]:
    q = set(query_tokens(query)); words=tokens(sentence); present=set(words)
    if not q or not words:return (0.,0.,0.)
    if re.search(r'(?i)how many|how much|what (?:percentage|year)|total length',query):
        if not re.search(r'\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|billion)\b',sentence,re.I):
            return (0.,0.,0.)
    shared=q & present
    # Query years are constraints, not optional relevance hints.
    years=set(re.findall(r'\b(?:19|20)\d{2}\b',query))
    if years and not years.issubset(set(re.findall(r'\b(?:19|20)\d{2}\b',sentence))):return (0.,0.,0.)
    weights=weights or {}
    unseen=max(weights.values(),default=1.)
    coverage=sum(weights.get(w,unseen) for w in shared)/sum(weights.get(w,unseen) for w in q)
    # Prefer a compact relation over scattered mentions in a longer sentence.
    positions=[(i,w) for i,w in enumerate(words) if w in shared]
    span=len(words)+1
    for start in range(len(positions)):
        seen=set()
        for end in range(start,len(positions)):
            seen.add(positions[end][1])
            if seen==shared:
                span=min(span,positions[end][0]-positions[start][0]+1);break
    proximity=len(shared)/span
    return (coverage,proximity,len(shared)/len(words))
