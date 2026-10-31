"""
main.py — FastAPI application entry point
Endpoints: GET /health, POST /extract, POST /search, GET /graph
"""
import json
import html
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import httpx
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

# ── Load data at module level & startup ──────────────────────────────────────
STORES_PATH = Path(__file__).parent / "data" / "stores.json"
STORES: list[dict] = json.loads(STORES_PATH.read_text()) if STORES_PATH.exists() else []
PRODUCTS: list[dict] = []
STORE_IMAGE_CACHE: dict[str, Optional[str]] = {}
STORE_IMAGE_CACHE_QUERY: Optional[str] = None

STORE_SEARCH_URLS = {
    "sapphireonline.pk": "https://pk.sapphireonline.pk/search?q={query}",
    "limelight.pk": "https://www.limelight.pk/search?q={query}",
    "khaadi.com": "https://global.khaadi.com/search?q={query}",
    "sanasafinaz.com": "https://www.sanasafinaz.com/pk/catalogsearch/result/?q={query}",
    "gulahmed.com": "https://www.gulahmedshop.com/catalogsearch/result/?q={query}",
    "jdotpk.com": "https://www.junaidjamshed.com/catalogsearch/result/?q={query}",
    "nishatlinen.com": "https://nishatlinen.com/search?q={query}",
    "alkaramstudio.com": "https://www.alkaramstudio.com/search?q={query}",
    "generation.com.pk": "https://generation.com.pk/search?q={query}",
    "ethnic.pk": "https://ethnic.pk/search?q={query}",
    "bonanzasatrangi.com": "https://bonanzasatrangi.com/search?q={query}",
    "mariab.pk": "https://www.mariab.pk/catalogsearch/result/?q={query}",
}

@app.on_event("startup")
async def startup():
    global PRODUCTS
    db.init_db()
    PRODUCTS = db.load_all_products()
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


def _extract_store_image(html_text: str) -> Optional[str]:
    candidates = re.findall(
        r'(?:https?:)?//[^"\'\s<>]+\.(?:jpg|jpeg|png|webp)(?:\?[^"\'\s<>]*)?',
        html_text,
        flags=re.IGNORECASE,
    )
    for candidate in candidates:
        image = html.unescape(candidate.replace("\\/", "/").strip())
        if image.startswith("//"):
            image = f"https:{image}"
        if image.startswith("http") and not any(
            word in image.lower()
            for word in (
                "logo", "icon", "placeholder", "unsplash", "700x105",
                "popup_bnpl", "live-chat", "menu-images", "payment",
                "footer", "trust-badge", "menu", "new-in", "banner",
                "collection", "lookbook", "thumbnail", "winter-prints",
            )
        ):
            return image
    return None


def _live_store_image(store: str, query: str) -> Optional[str]:
    template = STORE_SEARCH_URLS.get(store)
    if not template:
        return None
    try:
        response = httpx.get(
            template.format(query=quote_plus(query)),
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/120 Safari/537.36"
                )
            },
            follow_redirects=True,
            timeout=5,
        )
        if response.status_code != 200:
            return None
        return _extract_store_image(response.text)
    except httpx.HTTPError as error:
        print(f"[images] {store} unavailable: {error}")
        return None


def _live_store_images(stores: set[str], query_attrs: dict) -> dict[str, Optional[str]]:
    global STORE_IMAGE_CACHE_QUERY
    query = " ".join(
        value for value in (
            query_attrs.get("color"),
            query_attrs.get("silhouette"),
            query_attrs.get("length"),
            "dress",
        )
        if value and value != "unknown"
    )
    if STORE_IMAGE_CACHE_QUERY != query:
        STORE_IMAGE_CACHE.clear()
        STORE_IMAGE_CACHE_QUERY = query

    missing = [store for store in stores if store not in STORE_IMAGE_CACHE]
    if missing:
        with ThreadPoolExecutor(max_workers=6) as executor:
            fetched = executor.map(lambda store: (store, _live_store_image(store, query)), missing)
            STORE_IMAGE_CACHE.update(fetched)
    return {store: STORE_IMAGE_CACHE.get(store) for store in stores}


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
                color=p.get("color", "unknown"),
                price=price, currency=p.get("currency", "PKR"),
                image=p.get("image"), url=p["url"],
                score=round(sc * 100, 1), label=lbl,
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

    results = results[:20]
    live_images = _live_store_images({result.store for result in results}, query_attrs)
    for result in results:
        result.image = live_images.get(result.store)
    return results, relaxed_reasons


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

@app.get("/live-search")
async def live_regional_search(
    q: Optional[str] = "maxi dress",
    color: Optional[str] = "",
    silhouette: Optional[str] = ""
):
    """
    Constructs direct live search query URLs for all verified Pakistani apparel stores
    available in Islamabad & Rawalpindi.
    """
    search_term = " ".join(filter(None, [color, silhouette, q])).strip()
    results = []
    for s in STORES:
        query_url = f"{s.get('search_url', s.get('website') + '/search?q=')}{search_term.replace(' ', '+')}"
        results.append({
            "store": s["store"],
            "name": s["name"],
            "website": s.get("website", ""),
            "live_search_url": query_url,
            "branches": s.get("branches", [])
        })
    return {
        "search_term": search_term,
        "stores_count": len(results),
        "stores": results
    }

@app.get("/products/count")
async def products_count():
    return {"count": len(PRODUCTS)}


@app.get("/graph")
async def catalog_graph(
    store: Optional[str] = None,
    attribute: Optional[str] = None,
):
    """Return the product relationship graph derived from the catalog rows."""
    attribute_keys = ("silhouette", "neckline", "sleeve", "length", "color", "occasion")
    if attribute and attribute not in attribute_keys:
        raise HTTPException(400, f"Unsupported attribute: {attribute}")

    products = [p for p in PRODUCTS if not store or p["store"] == store]
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    edge_keys: set[tuple[str, str, str]] = set()

    def add_node(node_id: str, node_type: str, label: str, **data):
        nodes.setdefault(node_id, {
            "id": node_id,
            "type": node_type,
            "label": label,
            **data,
        })

    def add_edge(source: str, target: str, relation: str):
        key = (source, target, relation)
        if key not in edge_keys:
            edge_keys.add(key)
            edges.append({"source": source, "target": target, "relation": relation})

    for product in products:
        product_id = f"product:{product['id']}"
        add_node(
            product_id,
            "product",
            product["title"],
            product_id=product["id"],
            store=product["store"],
            store_name=product.get("store_name", product["store"]),
            price=product.get("price", 0),
            currency=product.get("currency", "PKR"),
            url=product["url"],
            image=product.get("image"),
        )

        store_id = f"store:{product['store']}"
        add_node(
            store_id,
            "store",
            product.get("store_name", product["store"]),
            domain=product["store"],
        )
        add_edge(product_id, store_id, "sold by")

        area = str(product.get("area") or "").strip()
        if area:
            area_id = f"area:{area.lower()}"
            add_node(area_id, "area", area)
            add_edge(product_id, area_id, "available in")

        for key in attribute_keys:
            if attribute and key != attribute:
                continue
            value = str(product.get(key) or "unknown").strip()
            if not value or value == "unknown":
                continue
            value_id = f"attribute:{key}:{value.lower()}"
            add_node(value_id, "attribute", value, attribute=key)
            add_edge(product_id, value_id, f"has {key}")

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "product_count": len(products),
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


# ── Dev runner ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
