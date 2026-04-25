"""Embedding generation for EthosOS vector memory.

Using sentence-transformers (MiniLM-L6-v2) for fast, lightweight embeddings.
"""

from __future__ import annotations

from typing import Any

import numpy as np


DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_SIZE = 384


class EmbeddingGenerator:
    """Generate embeddings using sentence-transformers."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str = "cpu",
        normalize: bool = True,
    ):
        """Initialize embedding generator.

        Args:
            model_name: HuggingFace model name
            device: Device to use (cpu, cuda, mps)
            normalize: Normalize embeddings to unit length
        """
        self._model_name = model_name
        self._device = device
        self._normalize = normalize
        self._model = None
        self._dim = None

    def _load_model(self) -> Any:
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self._model_name, device=self._device)
                self._dim = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self._dim is None:
            self._load_model()
        return self._dim or VECTOR_SIZE

    def encode(self, texts: str | list[str]) -> np.ndarray:
        """Encode texts to embeddings.

        Args:
            texts: Single text or list of texts

        Returns:
            Embedding array of shape (n, dimension)
        """
        model = self._load_model()

        if isinstance(texts, str):
            texts = [texts]

        embeddings = model.encode(
            texts,
            normalize_embeddings=self._normalize,
            show_progress_bar=False,
        )

        return embeddings

    def encode_batch(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Encode texts in batches.

        Args:
            texts: List of texts
            batch_size: Batch size for encoding

        Returns:
            Embedding array
        """
        model = self._load_model()

        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=self._normalize,
            show_progress_bar=True,
        )

        return embeddings

    def similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        embeddings = self.encode([text1, text2])
        emb1, emb2 = embeddings[0], embeddings[1]

        dot = np.dot(emb1, emb2)
        norm = np.linalg.norm(emb1) * np.linalg.norm(emb2)

        if norm == 0:
            return 0.0

        return float(dot / norm)


_embedding_generator: EmbeddingGenerator | None = None


def get_embedding_generator(
    model_name: str = DEFAULT_MODEL,
    device: str = "cpu",
) -> EmbeddingGenerator:
    """Get singleton embedding generator."""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator(model_name=model_name, device=device)
    return _embedding_generator


def encode_text(text: str) -> list[float]:
    """Quick encode single text to vector.

    Args:
        text: Text to encode

    Returns:
        Vector as list of floats
    """
    generator = get_embedding_generator()
    embedding = generator.encode(text)
    return embedding.tolist()


def encode_batch(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """Quick encode batch of texts.

    Args:
        texts: Texts to encode
        batch_size: Batch size

    Returns:
        List of vectors
    """
    generator = get_embedding_generator()
    embeddings = generator.encode_batch(texts, batch_size=batch_size)
    return embeddings.tolist()