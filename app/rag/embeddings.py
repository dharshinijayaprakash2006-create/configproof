"""Turn text into vectors. "fake" for tests and CI; "local" runs a free model on your CPU."""

import hashlib
import math
import re
from typing import Protocol

from app.config import Settings


class Embedder(Protocol):
    model: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class FakeEmbedder:
    """Offline and deterministic. Each word is hashed into one of `dim` buckets,
    so texts that share words get similar vectors. Good for tests, useless for meaning."""

    def __init__(self, dim: int = 384):
        self.model, self.dim = f"fake-{dim}", dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for text in texts:
            v = [0.0] * self.dim
            for word in re.findall(r"[a-z0-9]+", text.lower()):
                h = int(hashlib.md5(word.encode()).hexdigest(), 16)
                v[h % self.dim] += 1.0
            if not any(v):
                v[0] = 1.0  # never store a zero vector: cosine distance is undefined for it
            norm = math.sqrt(sum(x * x for x in v))
            out.append([x / norm for x in v])
        return out


class LocalEmbedder:
    """A sentence-transformers model on the CPU. Downloaded once from Hugging Face, then cached."""

    def __init__(self, model_name: str, dim: int, batch_size: int = 32):
        from sentence_transformers import SentenceTransformer  # imported here: CI never needs torch

        self._st = SentenceTransformer(model_name, device="cpu")
        self.model, self.dim, self.batch_size = model_name, dim, batch_size

    def embed(self, texts: list[str]) -> list[list[float]]:
        vecs = self._st.encode(
            texts, batch_size=self.batch_size, normalize_embeddings=True, show_progress_bar=False
        )
        if vecs.shape[1] != self.dim:
            raise ValueError(f"{self.model} gives {vecs.shape[1]} numbers, table expects {self.dim}")
        return vecs.tolist()


def get_embedder(settings: Settings) -> Embedder:
    if settings.embedding_provider == "local":
        return LocalEmbedder(settings.embedding_model, settings.embedding_dim)
    return FakeEmbedder(settings.embedding_dim)
