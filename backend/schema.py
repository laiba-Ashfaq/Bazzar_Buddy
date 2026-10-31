"""
schema.py — Pydantic contracts (the frozen API shape — everyone builds against this)
"""
from pydantic import BaseModel
from typing import Optional

# ── Controlled vocabulary ────────────────────────────────────────────────────
ALLOWED = {
    "silhouette": ["a-line", "straight", "fit-and-flare", "bodycon", "shift",
                   "wrap", "ballgown", "empire", "unknown"],
    "neckline":   ["round", "v-neck", "square", "boat", "halter",
                   "off-shoulder", "high-neck", "sweetheart", "unknown"],
    "sleeve":     ["sleeveless", "cap", "short", "three-quarter",
                   "full", "bell", "puff", "unknown"],
    "length":     ["mini", "knee", "midi", "maxi", "unknown"],
    "color":      ["red", "blue", "green", "black", "white", "pink", "yellow",
                   "beige", "brown", "grey", "purple", "orange", "multi", "unknown"],
    "occasion":   ["casual", "office", "formal", "wedding", "party", "unknown"],
}

ATTR_KEYS = list(ALLOWED.keys())

# ── /extract ─────────────────────────────────────────────────────────────────
class AttrValue(BaseModel):
    value: str
    conf: float

class ExtractResponse(BaseModel):
    attributes: dict[str, AttrValue]
    source: str           # "gemini" | "ollama" | "cache" | "mock"

# ── /search ──────────────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    attributes: dict[str, str]
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    area: Optional[str] = None          # "Islamabad" | "Rawalpindi" | "Online" | None

class DifferEntry(BaseModel):
    attr: str
    wanted: str
    got: str
    sim: float
    conflict: bool = False

class ProductResult(BaseModel):
    id: int
    title: str
    store: str
    price: float
    currency: str = "PKR"
    image: Optional[str]
    url: str
    score: float
    label: str            # "Close Match" | "Similar" | "Inspired-by"
    matched: list[str]
    differs: list[DifferEntry]
    explanation: str
    branches: list[str]

class SearchResponse(BaseModel):
    results: list[ProductResult]
    relaxed: list[str]    # e.g. ["budget +15%", "dropped: occasion"]

# ── /health ───────────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    products_loaded: int
    demo_mode: bool
