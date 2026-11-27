"""Vector embedding generator using Gemini embeddings with a deterministic hash-based fallback."""

import hashlib
import math
import re

from ..llm import embed_with_llm

EMBEDDING_DIM = 384


def embed_text(text: str) -> list[float]:
    """Generate a 384-dim vector embedding (uses Gemini gemini-embedding-001 if configured, else deterministic)."""
    llm_vec = embed_with_llm(text or "", dimensions=EMBEDDING_DIM)
    if llm_vec is not None:
        return llm_vec

    # Fall back to deterministic feature hashing when Gemini embeddings are unavailable
    vec = [0.0] * EMBEDDING_DIM
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    if not tokens:
        return vec

    # Combine unigrams and character trigrams for robust local similarity matching
    features = list(tokens)
    for tok in tokens:
        if len(tok) >= 3:
            features.extend(tok[i : i + 3] for i in range(len(tok) - 2))

    for feat in features:
        digest = hashlib.sha256(feat.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "little") % EMBEDDING_DIM
        sign = 1.0 if (digest[4] % 2 == 0) else -1.0
        vec[idx] += sign

    # L2-normalize the vector so cosine similarity works consistently
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec
