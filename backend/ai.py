"""
ai.py — Gemini Flash + Ollama vision calls with automatic fallback
"""
import base64, hashlib, json, os, re
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/{model}:generateContent"
)

CACHE_DIR = Path(__file__).parent.parent / "demo" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── Prompt ───────────────────────────────────────────────────────────────────
EXTRACT_PROMPT = """You analyze fashion sketches or dress photos.
Return ONLY valid JSON with these exact keys:
silhouette, neckline, sleeve, length, color, occasion.

Each value MUST be: {"value": "<string>", "conf": <0.0-1.0>}

Allowed values:
- silhouette: a-line, straight, fit-and-flare, bodycon, shift, wrap, ballgown, empire
- neckline:   round, v-neck, square, boat, halter, off-shoulder, high-neck, sweetheart
- sleeve:     sleeveless, cap, short, three-quarter, full, bell, puff
- length:     mini, knee, midi, maxi
- color:      red, blue, green, black, white, pink, yellow, beige, brown, grey, purple, orange, multi
- occasion:   casual, office, formal, wedding, party

Rules:
- If an attribute is not clearly visible, use "unknown" with conf 0.0
- Do NOT invent values outside the allowed lists
- Do NOT add extra keys
- Return ONLY the JSON object, no markdown fences"""


# ── Cache helpers ─────────────────────────────────────────────────────────────
def _cache_key(image_bytes: bytes) -> str:
    return hashlib.sha1(image_bytes).hexdigest()

def _load_cache(key: str) -> dict | None:
    p = CACHE_DIR / f"{key}.json"
    if p.exists():
        return json.loads(p.read_text())
    return None

def _save_cache(key: str, data: dict):
    (CACHE_DIR / f"{key}.json").write_text(json.dumps(data, indent=2))


# ── Gemini ────────────────────────────────────────────────────────────────────
def extract_gemini(image_bytes: bytes, mime: str, text: str = "") -> dict:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    model   = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY not set")

    url = GEMINI_URL.format(model=model)
    prompt = EXTRACT_PROMPT + (f"\n\nUser note: {text}" if text else "")
    parts = [{"text": prompt}]
    if image_bytes:
        parts.append({
            "inline_data": {
                "mime_type": mime,
                "data": base64.b64encode(image_bytes).decode()
            }
        })

    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2,
            "maxOutputTokens": 512,
        },
    }

    r = httpx.post(
        url,
        json=body,
        headers={"x-goog-api-key": api_key},
        timeout=60,
    )
    r.raise_for_status()
    raw = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(raw)


# ── Ollama ────────────────────────────────────────────────────────────────────
def extract_ollama(image_bytes: bytes, text: str = "") -> dict:
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    model      = os.environ.get("OLLAMA_MODEL", "llava:7b")
    prompt     = EXTRACT_PROMPT + (f"\n\nUser note: {text}" if text else "")

    msg: dict = {"role": "user", "content": prompt}
    if image_bytes:
        msg["images"] = [base64.b64encode(image_bytes).decode()]

    r = httpx.post(
        f"{ollama_url}/api/chat",
        json={
            "model": model,
            "messages": [msg],
            "stream": False,
            "format": "json",
        },
        timeout=180,
    )
    r.raise_for_status()
    content = r.json()["message"]["content"]
    # Strip markdown fences if model wraps output
    content = re.sub(r"```json\s*|\s*```", "", content).strip()
    return json.loads(content)


# ── Mock fallback (text-only, no AI needed) ───────────────────────────────────
MOCK_RESPONSE = {
    "silhouette": {"value": "a-line",    "conf": 0.75},
    "neckline":   {"value": "v-neck",    "conf": 0.70},
    "sleeve":     {"value": "full",      "conf": 0.80},
    "length":     {"value": "maxi",      "conf": 0.65},
    "color":      {"value": "green",     "conf": 0.60},
    "occasion":   {"value": "formal",    "conf": 0.55},
}


# ── Public entry point ────────────────────────────────────────────────────────
def extract(image_bytes: bytes, mime: str = "image/jpeg", text: str = "") -> dict:
    """
    Returns {"attributes": {...}, "source": "gemini"|"ollama"|"cache"|"mock"}
    Tries: cache → Gemini → Ollama → mock
    """
    # 1. Cache (for DEMO_MODE or repeated calls)
    key = _cache_key(image_bytes)
    cached = _load_cache(key)
    if cached:
        return {"attributes": cached["attributes"], "source": "cache"}

    demo_mode = os.environ.get("DEMO_MODE", "0") == "1"

    # 2. Gemini
    if not demo_mode:
        try:
            attrs = extract_gemini(image_bytes, mime, text)
            _save_cache(key, {"attributes": attrs})
            return {"attributes": attrs, "source": "gemini"}
        except Exception as e:
            print(f"[ai] Gemini failed: {e}")

        # 3. Ollama
        try:
            attrs = extract_ollama(image_bytes, text)
            _save_cache(key, {"attributes": attrs})
            return {"attributes": attrs, "source": "ollama"}
        except Exception as e:
            print(f"[ai] Ollama failed: {e}")

    # 4. Mock (always works)
    print("[ai] Using mock response")
    return {"attributes": MOCK_RESPONSE, "source": "mock"}
