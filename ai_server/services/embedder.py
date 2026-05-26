from __future__ import annotations

from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


@lru_cache
def get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> List[float]:
    model = get_model()
    embedding = model.encode([text], normalize_embeddings=True)[0]
    return embedding.tolist()
