"""Visual product matching with a persisted CLIP embedding index."""

from __future__ import annotations

import io
import logging
import sqlite3
from pathlib import Path
from typing import Any

import httpx
import numpy as np
from PIL import Image, UnidentifiedImageError

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # type: ignore[assignment,misc]

DB_PATH = Path(__file__).parent / "data" / "products.db"
INDEX_PATH = Path(__file__).parent / "data" / "embeddings.npz"
MODEL_NAME = "clip-ViT-B-32"
MAX_IMAGE_SIZE = 512
DOWNLOAD_TIMEOUT = 20.0

logger = logging.getLogger(__name__)
_MODEL = None


def _model():
    global _MODEL
    if SentenceTransformer is None:
        raise RuntimeError(
            "CLIP support is optional. Install backend/requirements-visual.txt "
            "before building or querying the visual index."
        )
    if _MODEL is None:
        _MODEL = SentenceTransformer(MODEL_NAME, device="cpu")
    return _MODEL


def _product_rows() -> list[dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute("SELECT * FROM products")]


def _load_image(url: str) -> Image.Image:
    response = httpx.get(
        url,
        headers={"User-Agent": "BazzarBuddy/1.0 product image indexer"},
        follow_redirects=True,
        timeout=DOWNLOAD_TIMEOUT,
    )
    response.raise_for_status()
    with Image.open(io.BytesIO(response.content)) as image:
        image = image.convert("RGB")
        image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
        return image.copy()


def _embedding(image: Image.Image | bytes) -> np.ndarray:
    if isinstance(image, bytes):
        with Image.open(io.BytesIO(image)) as opened:
            image = opened.convert("RGB")
            image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
            image = image.copy()
    vector = np.asarray(_model().encode(image, convert_to_numpy=True), dtype=np.float32)
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("model returned a zero-length embedding")
    return vector / norm


def build_index() -> int:
    """Download catalog images, embed them, and save product IDs plus vectors."""
    rows = _product_rows()
    ids: list[int] = []
    vectors: list[np.ndarray] = []
    skipped = 0

    for row in rows:
        try:
            image_url = row.get("image")
            if not image_url:
                raise ValueError("missing image URL")
            image = _load_image(str(image_url))
            ids.append(int(row["id"]))
            vectors.append(_embedding(image))
        except (httpx.HTTPError, OSError, UnidentifiedImageError, ValueError) as error:
            skipped += 1
            logger.warning("Skipping product %s (%s): %s", row.get("id"), row.get("title"), error)

    if not vectors:
        raise RuntimeError("No product images could be indexed")

    np.savez_compressed(
        INDEX_PATH,
        ids=np.asarray(ids, dtype=np.int64),
        vectors=np.vstack(vectors).astype(np.float32),
    )
    logger.info("Indexed %d product images; skipped %d", len(ids), skipped)
    return len(ids)


def _load_index() -> tuple[np.ndarray, np.ndarray]:
    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            f"{INDEX_PATH} does not exist. Run build_index() before find_similar()."
        )
    with np.load(INDEX_PATH) as index:
        return index["ids"].astype(np.int64), index["vectors"].astype(np.float32)


def find_similar(
    image_bytes: bytes,
    k: int = 10,
    brand_domain: str | None = None,
) -> list[dict[str, Any]]:
    """Return top catalog products by cosine similarity to an uploaded image."""
    if not image_bytes:
        raise ValueError("image_bytes must not be empty")
    if k < 1:
        raise ValueError("k must be at least 1")

    ids, vectors = _load_index()
    rows_by_id = {int(row["id"]): row for row in _product_rows()}
    query_vector = _embedding(image_bytes)
    scores = vectors @ query_vector

    candidates = []
    for index, product_id in enumerate(ids):
        row = rows_by_id.get(int(product_id))
        if row is None:
            continue
        if brand_domain and row["store"] != brand_domain:
            continue
        candidates.append((float(scores[index]), row))

    candidates.sort(key=lambda item: item[0], reverse=True)
    results = []
    for score, row in candidates[:k]:
        result = dict(row)
        result["visual_score"] = score
        results.append(result)
    return results
