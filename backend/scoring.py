"""
scoring.py — Attribute matching + near-miss graph
"""
import json
from pathlib import Path

# ── Load similarity tables ────────────────────────────────────────────────────
_DATA = Path(__file__).parent / "data"

def _load_sim():
    p = _DATA / "similarity.json"
    if p.exists():
        raw = json.loads(p.read_text())
        out = {}
        for attr, pairs in raw.items():
            if attr.startswith("_") or not isinstance(pairs, dict):
                continue
            out[attr] = {}
            for key, val in pairs.items():
                if "|" in key:
                    parts = key.split("|")
                    if len(parts) == 2:
                        a, b = sorted(parts)
                        out[attr][f"{a}|{b}"] = val
        return out
    return {}

def _load_conflicts():
    p = _DATA / "similarity.json"
    if not p.exists():
        return {}
    raw = json.loads(p.read_text())
    return raw.get("_conflicts", {})

SIM_TABLE  = _load_sim()
CONFLICTS  = _load_conflicts()

# ── Weights per attribute (Color & Silhouette prioritized for visual accuracy) ──
WEIGHTS = {
    "color":      0.30,
    "silhouette": 0.25,
    "length":     0.18,
    "neckline":   0.12,
    "sleeve":     0.10,
    "occasion":   0.05,
}

LABEL_THRESHOLDS = [
    (0.85, "Close Match"),
    (0.60, "Similar"),
    (0.00, "Inspired-by"),
]


# ── Similarity between two attribute values ───────────────────────────────────
def _sim(attr: str, a: str, b: str) -> float:
    """Return similarity 0-1 (or -1 if hard conflict)."""
    if a == b:
        return 1.0
    if not a or a == "unknown" or not b or b == "unknown":
        return 0.0
    key = "|".join(sorted([a, b]))
    # Check hard conflict
    if key in CONFLICTS.get(attr, []):
        return -1.0
    return SIM_TABLE.get(attr, {}).get(key, 0.0)


# ── Main scoring function ─────────────────────────────────────────────────────
def score(query: dict, product: dict) -> tuple[float, list, list]:
    """
    Returns (score 0-1, matched_attrs, differs_list)
    query and product are both plain dicts of {attr: value_string}
    """
    total_weight = 0.0
    weighted_sim = 0.0
    matched = []
    differs = []

    for attr, weight in WEIGHTS.items():
        want = query.get(attr, "unknown")
        if not want or want == "unknown":
            continue                          # skip attrs the sketch couldn't determine
        total_weight += weight
        have = product.get(attr, "unknown") or "unknown"

        s = _sim(attr, want, have)

        if s < 0:                             # hard conflict
            differs.append({
                "attr": attr, "wanted": want, "got": have,
                "sim": 0.0, "conflict": True,
            })
        elif s == 1.0:
            weighted_sim += weight
            matched.append(attr)
        elif s > 0:
            weighted_sim += weight * s
            differs.append({
                "attr": attr, "wanted": want, "got": have,
                "sim": round(s, 2), "conflict": False,
            })
        else:
            differs.append({
                "attr": attr, "wanted": want, "got": have,
                "sim": 0.0, "conflict": False,
            })

    final_score = (weighted_sim / total_weight) if total_weight else 0.0
    return round(final_score, 4), matched, differs


def label(score_val: float) -> str:
    for threshold, lbl in LABEL_THRESHOLDS:
        if score_val >= threshold:
            return lbl
    return "Inspired-by"


def explain(matched: list, differs: list, n_total: int) -> str:
    parts = [f"Matches {len(matched)} of {n_total} attributes."]
    for d in differs:
        if d.get("conflict"):
            parts.append(
                f"{d['attr'].capitalize()}: '{d['got']}' conflicts with wanted '{d['wanted']}'."
            )
        elif d["sim"] >= 0.5:
            parts.append(
                f"{d['attr'].capitalize()} is {d['got'] or 'unknown'} "
                f"instead of {d['wanted']} (similar)."
            )
        elif d["sim"] > 0:
            parts.append(
                f"{d['attr'].capitalize()} is {d['got'] or 'unknown'} "
                f"instead of {d['wanted']} (different)."
            )
        else:
            parts.append(
                f"{d['attr'].capitalize()}: wanted {d['wanted']}, got {d['got'] or 'unknown'}."
            )
    return " ".join(parts)
