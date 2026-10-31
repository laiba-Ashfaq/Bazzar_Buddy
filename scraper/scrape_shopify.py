"""
scrape_shopify.py — Shopify products.json Scraper for Pakistani Fashion Stores

Usage:
    python scraper/scrape_shopify.py khaadi.com
    python scraper/scrape_shopify.py sanasafinaz.com dresses
    python scraper/scrape_shopify.py gulahmedshop.com
"""

import sys
import json
import time
from pathlib import Path
import httpx

RAW_DIR = Path(__file__).parent / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Common Shopify Pakistani Fashion Domains
KNOWN_STORES = [
    "khaadi.com",
    "sanasafinaz.com",
    "gulahmedshop.com",
    "bonanzasatrangi.com",
    "alkaramstudio.com",
    "nishatlinen.com",
    "generation.com.pk"
]

def scrape_store(domain: str, collection: str = None, max_pages: int = 3):
    """Scrapes products.json from Shopify endpoints."""
    base_url = f"https://{domain}"
    path = f"/collections/{collection}/products.json" if collection else "/products.json"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    products = []
    print(f"[*] Scraping {base_url}{path} (up to {max_pages} pages)...")
    
    client = httpx.Client(timeout=25.0, headers=headers, follow_redirects=True)
    
    for page in range(1, max_pages + 1):
        try:
            url = f"{base_url}{path}"
            params = {"limit": 50, "page": page}
            res = client.get(url, params=params)
            
            if res.status_code != 200:
                print(f"[-] Page {page} returned status {res.status_code}. Stopping.")
                break
                
            data = res.json()
            items = data.get("products", [])
            if not items:
                print(f"[-] No more products on page {page}.")
                break
                
            for p in items:
                # Extract clean variant details
                price = None
                if p.get("variants") and len(p["variants"]) > 0:
                    try:
                        price = float(p["variants"][0].get("price", 0))
                    except (ValueError, TypeError):
                        price = 0.0
                
                image_url = p["images"][0]["src"] if p.get("images") and len(p["images"]) > 0 else None
                
                products.append({
                    "store": domain,
                    "title": p.get("title", ""),
                    "handle": p.get("handle", ""),
                    "url": f"{base_url}/products/{p.get('handle', '')}",
                    "type": p.get("product_type", ""),
                    "tags": p.get("tags", []),
                    "price": price,
                    "currency": "PKR",
                    "image": image_url,
                    "body_html": p.get("body_html", "")[:300] if p.get("body_html") else ""
                })
                
            print(f"[+] Page {page}: Fetched {len(items)} products (Total: {len(products)})")
            time.sleep(1.2)  # Respectful rate limiting
            
        except Exception as e:
            print(f"[!] Error on page {page}: {e}")
            break
            
    client.close()
    
    out_file = RAW_DIR / f"{domain.replace('.', '_')}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
        
    print(f"[✓] Saved {len(products)} products to {out_file}")
    return products

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "khaadi.com"
    collection = sys.argv[2] if len(sys.argv) > 2 else None
    scrape_store(target, collection)
