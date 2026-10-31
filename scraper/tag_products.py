"""
tag_products.py — Auto-tag scraped dresses into standard attributes
Supports:
1. Rule-based keyword extraction (fast, zero dependency)
2. Ollama LLM extraction (when Ollama is active)
"""

import os
import re
import json
import sqlite3
from pathlib import Path

RAW_DIR = Path(__file__).parent / "raw"
DB_PATH = Path(__file__).parent.parent / "backend" / "data" / "products.db"

# Keyword dictionary for instant zero-dependency tagging
KEYWORDS = {
    "silhouette": {
        "a-line": ["a-line", "aline", "flared", "flare"],
        "straight": ["straight", "kurta", "kurti", "tunic"],
        "fit-and-flare": ["fit and flare", "skater"],
        "bodycon": ["bodycon", "fitted", "tight"],
        "shift": ["shift", "box", "loose"],
        "wrap": ["wrap", "angrakha", "overlap"],
        "ballgown": ["ballgown", "bridal", "lehenga", "frock", "peshwas"],
        "empire": ["empire", "gather"]
    },
    "neckline": {
        "v-neck": ["v-neck", "v neck", "v-slit"],
        "round": ["round neck", "crew", "scoop", "round"],
        "square": ["square"],
        "boat": ["boat neck", "boat"],
        "halter": ["halter"],
        "off-shoulder": ["off shoulder", "off-shoulder", "cold shoulder"],
        "high-neck": ["high neck", "collar", "mandarin", "band", "ban"],
        "sweetheart": ["sweetheart"]
    },
    "sleeve": {
        "sleeveless": ["sleeveless", "without sleeve"],
        "cap": ["cap sleeve"],
        "short": ["short sleeve", "half sleeve"],
        "three-quarter": ["three quarter", "3/4", "quarter sleeve"],
        "full": ["full sleeve", "long sleeve", "full sleeves"],
        "bell": ["bell sleeve", "flared sleeve"],
        "puff": ["puff sleeve", "gathered sleeve"]
    },
    "length": {
        "maxi": ["maxi", "floor", "ankle", "long"],
        "midi": ["midi", "calf"],
        "knee": ["knee length", "short kurta", "knee"],
        "mini": ["mini", "short dress", "above knee"]
    },
    "color": {
        "red": ["red", "crimson", "ruby", "maroon", "burgundy", "scarlet"],
        "blue": ["blue", "navy", "teal", "turquoise", "indigo", "cyan", "azure", "cobalt"],
        "green": ["green", "emerald", "olive", "mint", "sage", "pistachio"],
        "black": ["black", "charcoal", "ebony"],
        "white": ["white", "ivory", "cream", "off-white", "pearl"],
        "pink": ["pink", "rose", "blush", "magenta", "coral", "peach"],
        "yellow": ["yellow", "mustard", "lemon", "ochre", "gold"],
        "beige": ["beige", "tan", "khaki", "camel", "nude"],
        "brown": ["brown", "coffee", "chocolate", "mocha"],
        "grey": ["grey", "gray", "silver", "slate"],
        "purple": ["purple", "lavender", "violet", "lilac", "plum"],
        "orange": ["orange", "rust", "terracotta", "tangerine"],
        "multi": ["multi", "print", "printed", "floral", "geometric", "pattern"]
    },
    "occasion": {
        "wedding": ["wedding", "bridal", "festive", "embroidered", "zari", "heavy", "velvet"],
        "formal": ["formal", "chiffon", "silk", "organza", "jacquard", "evening"],
        "casual": ["casual", "lawn", "cotton", "linen", "daily", "printed", "basic"],
        "party": ["party", "sequin", "glam", "satin"],
        "office": ["office", "solid", "minimal", "formal shirt"]
    }
}

def extract_by_rules(text: str) -> dict:
    text_lower = text.lower()
    result = {}
    for attr, mapping in KEYWORDS.items():
        found = "unknown"
        for val, triggers in mapping.items():
            if any(t in text_lower for t in triggers):
                found = val
                break
        result[attr] = found
    return result

def tag_file_to_db(raw_file: Path):
    if not raw_file.exists():
        print(f"File not found: {raw_file}")
        return
        
    with open(raw_file, "r", encoding="utf-8") as f:
        products = json.load(f)
        
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    
    saved = 0
    for p in products:
        full_text = f"{p.get('title', '')} {' '.join(p.get('tags', []))} {p.get('type', '')} {p.get('body_html', '')}"
        tags = extract_by_rules(full_text)
        
        cur.execute("""
            INSERT INTO products (store, title, url, image, price, currency, silhouette, neckline, sleeve, length, color, occasion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p.get("store"),
            p.get("title"),
            p.get("url"),
            p.get("image"),
            p.get("price") or 0.0,
            p.get("currency", "PKR"),
            tags["silhouette"],
            tags["neckline"],
            tags["sleeve"],
            tags["length"],
            tags["color"],
            tags["occasion"]
        ))
        saved += 1
        
    conn.commit()
    conn.close()
    print(f"[✓] Tagged & imported {saved} items from {raw_file.name} to {DB_PATH.name}")

if __name__ == "__main__":
    files = list(RAW_DIR.glob("*.json"))
    if not files:
        print("[!] No raw json files in scraper/raw/. Run scrape_shopify.py first.")
    else:
        for f in files:
            tag_file_to_db(f)
