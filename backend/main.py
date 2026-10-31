"""
main.py — FastAPI application entry point
Endpoints: GET /health, POST /extract, POST /search
"""
import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Load env before importing internal modules ────────────────────────────────
load_dotenv(Path(__file__).parent.parent / ".env")

import ai
import db
import scoring
from schema import (
    ALLOWED, ATTR_KEYS,
    DifferEntry, ExtractResponse, HealthResponse,
    ProductResult, SearchRequest, SearchResponse,
)

# ── App init ──────────────────────────────────────────────────────────────────
app = FastAPI(title="AI Fashion Styler API", version="1.0.0")

# CORS — allow the Vite dev server and the static landing page
FRONTEND_ORIGINS = [
    os.environ.get("FRONTEND_URL", "http://localhost:5173"),
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "null",   # file:// origin used when opening index.html directly
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # open for hackathon; tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load data at startup ──────────────────────────────────────────────────────
STORES: list[dict] = []
PRODUCTS: list[dict] = []

@app.on_event("startup")
async def startup():
    global STORES, PRODUCTS
    db.init_db()
    PRODUCTS = db.load_all_products()

    stores_path = Path(__file__).parent / "data" / "stores.json"
    if stores_path.exists():
        STORES = json.loads(stores_path.read_text())

    print(f"[startup] {len(PRODUCTS)} products | {len(STORES)} stores loaded")


# ── Helpers ───────────────────────────────────────────────────────────────────
def _validate_attrs(attrs: dict) -> dict:
    """Coerce values not in the allowed list to 'unknown'."""
    clean = {}
    for attr in ATTR_KEYS:
        val = attrs.get(attr, {})
        if isinstance(val, dict):
            val = val.get("value", "unknown")
        val = str(val).lower().strip()
        if val not in ALLOWED.get(attr, []):
            val = "unknown"
        clean[attr] = val
    return clean


def _branches_for_store(store_domain: str, area: Optional[str]) -> list[str]:
    for s in STORES:
        if s["store"] == store_domain:
            if not area or area == "Online":
                if area == "Online":
                    return ["Online delivery"] if s.get("delivers_online") else []
                return [b["label"] for b in s.get("branches", [])]
            filtered = [b["label"] for b in s.get("branches", []) if b["area"] == area]
            if not filtered and s.get("delivers_online"):
                filtered = ["Online delivery"]
            return filtered
    return []


def _area_match(store_domain: str, area: Optional[str]) -> bool:
    if not area:
        return True
    for s in STORES:
        if s["store"] == store_domain:
            if area == "Online":
                return bool(s.get("delivers_online"))
            has_branch = any(b["area"] == area for b in s.get("branches", []))
            delivers   = bool(s.get("delivers_online"))
            return has_branch or delivers
    return True   # unknown store — include


def _search_products(
    query_attrs: dict,
    budget_min: Optional[float],
    budget_max: Optional[float],
    area: Optional[str],
) -> tuple[list[ProductResult], list[str]]:
    relaxed_reasons: list[str] = []

    def _run(bmin, bmax, drop_attrs=None):
        q = dict(query_attrs)
        if drop_attrs:
            for a in drop_attrs:
                q[a] = "unknown"

        results = []
        for p in PRODUCTS:
            # Budget filter
            price = p.get("price", 0) or 0
            if bmin and price < bmin:
                continue
            if bmax and price > bmax:
                continue
            # Area filter
            if not _area_match(p["store"], area):
                continue

            sc, matched, differs = scoring.score(q, p)
            n_total = sum(1 for a in ATTR_KEYS if q.get(a) and q[a] != "unknown")
            lbl = scoring.label(sc)
            expl = scoring.explain(matched, differs, n_total)
            branches = _branches_for_store(p["store"], area)

            results.append(ProductResult(
                id=p["id"], title=p["title"], store=p["store"],
                price=price, currency=p.get("currency", "PKR"),
                image=p.get("image"), url=p["url"],
                score=sc, label=lbl,
                matched=matched,
                differs=[DifferEntry(**d) for d in differs],
                explanation=expl,
                branches=branches,
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results

    results = _run(budget_min, budget_max)

    # Relaxation: if < 5 results, widen budget by 15%
    if len(results) < 5 and (budget_min or budget_max):
        new_min = (budget_min * 0.85) if budget_min else None
        new_max = (budget_max * 1.15) if budget_max else None
        results = _run(new_min, new_max)
        relaxed_reasons.append("budget ±15%")

    # Relaxation: if still < 5, drop occasion
    if len(results) < 5:
        results = _run(budget_min, budget_max, drop_attrs=["occasion"])
        relaxed_reasons.append("dropped: occasion")

    # Relaxation: if still < 5, drop color
    if len(results) < 5:
        results = _run(budget_min, budget_max, drop_attrs=["occasion", "color"])
        relaxed_reasons.append("dropped: color")

    return results[:20], relaxed_reasons


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        products_loaded=len(PRODUCTS),
        demo_mode=os.environ.get("DEMO_MODE", "0") == "1",
    )


@app.post("/extract", response_model=ExtractResponse)
async def extract(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
):
    image_bytes = b""
    mime = "image/jpeg"

    if file:
        image_bytes = await file.read()
        mime = file.content_type or "image/jpeg"
        if len(image_bytes) > 10 * 1024 * 1024:   # 10 MB limit
            raise HTTPException(413, "Image too large. Max 10 MB.")

    if not image_bytes and not text:
        raise HTTPException(400, "Provide an image file or a text description.")

    try:
        result = ai.extract(image_bytes, mime, text or "")
    except Exception as e:
        raise HTTPException(500, f"AI extraction failed: {e}")

    # Validate / coerce attributes
    raw_attrs = result.get("attributes", {})
    validated = {}
    for attr in ATTR_KEYS:
        val = raw_attrs.get(attr, {})
        if isinstance(val, dict):
            value = val.get("value", "unknown")
            conf  = val.get("conf", 0.0)
        else:
            value, conf = str(val), 0.5
        if value not in ALLOWED.get(attr, []):
            value = "unknown"
        validated[attr] = {"value": value, "conf": conf}

    return ExtractResponse(attributes=validated, source=result.get("source", "unknown"))


@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    try:
        query_attrs = _validate_attrs(req.attributes)
        results, relaxed = _search_products(
            query_attrs, req.budget_min, req.budget_max, req.area
        )
        return SearchResponse(results=results, relaxed=relaxed)
    except Exception as e:
        raise HTTPException(500, f"Search failed: {e}")


@app.get("/stores")
async def list_stores():
    return STORES


@app.get("/products/count")
async def products_count():
    return {"count": len(PRODUCTS)}


# ── Dev runner ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
