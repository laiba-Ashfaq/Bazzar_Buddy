"""
db.py — SQLite helpers with extensive catalog for Islamabad & Rawalpindi apparel stores
"""
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "products.db"
STORES_PATH = Path(__file__).parent / "data" / "stores.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    store      TEXT NOT NULL,
    store_name TEXT NOT NULL,
    title      TEXT NOT NULL,
    url        TEXT NOT NULL,
    image      TEXT,
    price      REAL DEFAULT 0,
    currency   TEXT DEFAULT 'PKR',
    silhouette TEXT DEFAULT 'unknown',
    neckline   TEXT DEFAULT 'unknown',
    sleeve     TEXT DEFAULT 'unknown',
    length     TEXT DEFAULT 'unknown',
    color      TEXT DEFAULT 'unknown',
    occasion   TEXT DEFAULT 'unknown',
    area       TEXT DEFAULT 'Islamabad',
    branch     TEXT DEFAULT 'Centaurus Mall, Islamabad'
);
"""

# Extensive multi-store inventory covering all colors, cuts, and 12 Twin Cities brands
EXPANDED_PRODUCTS = [
    # ── SAPPHIRE (pk.sapphireonline.pk) ───────────────────────────────────────
    {"store":"sapphireonline.pk","store_name":"Sapphire","title":"Emerald Embroidered Lawn Maxi","url":"https://pk.sapphireonline.pk/search?q=emerald+maxi","image":"https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=500&q=80","price":8490,"silhouette":"a-line","neckline":"v-neck","sleeve":"full","length":"maxi","color":"green","occasion":"formal","area":"Islamabad","branch":"Centaurus Mall, F-8 Islamabad"},
    {"store":"sapphireonline.pk","store_name":"Sapphire","title":"Cobalt Blue Printed Kurti","url":"https://pk.sapphireonline.pk/search?q=blue+kurti","image":"https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=500&q=80","price":3990,"silhouette":"straight","neckline":"round","sleeve":"three-quarter","length":"knee","color":"blue","occasion":"casual","area":"Islamabad","branch":"Beverly Centre, Blue Area"},
    {"store":"sapphireonline.pk","store_name":"Sapphire","title":"Ruby Red Chiffon Festive Maxi","url":"https://pk.sapphireonline.pk/search?q=red+maxi","image":"https://images.unsplash.com/photo-1568252542512-9fe8fe9c87bb?w=500&q=80","price":13990,"silhouette":"a-line","neckline":"sweetheart","sleeve":"full","length":"maxi","color":"red","occasion":"wedding","area":"Rawalpindi","branch":"Saddar Cantt, Rawalpindi"},
    {"store":"sapphireonline.pk","store_name":"Sapphire","title":"Ivory Raw Silk Fit & Flare","url":"https://pk.sapphireonline.pk/search?q=ivory+dress","image":"https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=500&q=80","price":11500,"silhouette":"fit-and-flare","neckline":"square","sleeve":"sleeveless","length":"midi","color":"white","occasion":"formal","area":"Islamabad","branch":"Giga Mall, DHA Phase 2"},
    {"store":"sapphireonline.pk","store_name":"Sapphire","title":"Blush Pink Floral Shift","url":"https://pk.sapphireonline.pk/search?q=pink+shift","image":"https://images.unsplash.com/photo-1512436991641-6745cdb1723f?w=500&q=80","price":5490,"silhouette":"shift","neckline":"boat","sleeve":"short","length":"knee","color":"pink","occasion":"casual","area":"Rawalpindi","branch":"Bahria Town Phase 7"},
    {"store":"sapphireonline.pk","store_name":"Sapphire","title":"Noir Jet Black Velvet Gown","url":"https://pk.sapphireonline.pk/search?q=black+velvet","image":"https://images.unsplash.com/photo-1583744946564-b52ac1c389c8?w=500&q=80","price":18900,"silhouette":"straight","neckline":"high-neck","sleeve":"full","length":"maxi","color":"black","occasion":"formal","area":"Islamabad","branch":"Centaurus Mall, F-8 Islamabad"},

    # ── LIMELIGHT (limelight.pk) ──────────────────────────────────────────────
    {"store":"limelight.pk","store_name":"Limelight","title":"Sage Green Jacquard A-Line","url":"https://www.limelight.pk/search?q=green+jacquard","image":"https://images.unsplash.com/photo-1502716119720-b23a93e5fe1b?w=500&q=80","price":4850,"silhouette":"a-line","neckline":"v-neck","sleeve":"full","length":"midi","color":"green","occasion":"casual","area":"Islamabad","branch":"Centaurus Mall, F-8 Islamabad"},
    {"store":"limelight.pk","store_name":"Limelight","title":"Mustard Georgette Peshwas","url":"https://www.limelight.pk/search?q=mustard+frock","image":"https://images.unsplash.com/photo-1509631179647-0177331693ae?w=500&q=80","price":6990,"silhouette":"ballgown","neckline":"round","sleeve":"bell","length":"maxi","color":"yellow","occasion":"festive","area":"Islamabad","branch":"F-10 Markaz, Islamabad"},
    {"store":"limelight.pk","store_name":"Limelight","title":"Navy Blue Minimal Solid Shirt","url":"https://www.limelight.pk/search?q=navy+solid","image":"https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=500&q=80","price":2990,"silhouette":"straight","neckline":"boat","sleeve":"three-quarter","length":"knee","color":"blue","occasion":"office","area":"Rawalpindi","branch":"Commercial Market, Satellite Town"},
    {"store":"limelight.pk","store_name":"Limelight","title":"Coral Pink Printed Lawn Maxi","url":"https://www.limelight.pk/search?q=coral+maxi","image":"https://images.unsplash.com/photo-1545291730-faff8ca1d4b0?w=500&q=80","price":5200,"silhouette":"a-line","neckline":"sweetheart","sleeve":"puff","length":"maxi","color":"pink","occasion":"casual","area":"Rawalpindi","branch":"Saddar, Rawalpindi"},
    {"store":"limelight.pk","store_name":"Limelight","title":"Black Sequin Evening Dress","url":"https://www.limelight.pk/search?q=black+sequin","image":"https://images.unsplash.com/photo-1470259078422-826894b933aa?w=500&q=80","price":7490,"silhouette":"bodycon","neckline":"v-neck","sleeve":"sleeveless","length":"mini","color":"black","occasion":"party","area":"Islamabad","branch":"Giga Mall, Islamabad"},

    # ── KHAADI (khaadi.com) ───────────────────────────────────────────────────
    {"store":"khaadi.com","store_name":"Khaadi","title":"Emerald Chiffon Luxury Maxi","url":"https://khaadi.com/search?q=emerald+maxi","image":"https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=500&q=80","price":8900,"silhouette":"a-line","neckline":"v-neck","sleeve":"full","length":"maxi","color":"green","occasion":"formal","area":"Islamabad","branch":"Centaurus Mall, F-8 Islamabad"},
    {"store":"khaadi.com","store_name":"Khaadi","title":"Ivory Hand-Embroidered Kurta","url":"https://khaadi.com/search?q=ivory+kurta","image":"https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=500&q=80","price":6500,"silhouette":"straight","neckline":"round","sleeve":"full","length":"knee","color":"white","occasion":"casual","area":"Islamabad","branch":"F-7 Markaz (Jinnah Super)"},
    {"store":"khaadi.com","store_name":"Khaadi","title":"Teal Green Chiffon Wrap","url":"https://khaadi.com/search?q=teal+wrap","image":"https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&q=80","price":7800,"silhouette":"wrap","neckline":"v-neck","sleeve":"full","length":"maxi","color":"green","occasion":"formal","area":"Rawalpindi","branch":"Saddar, Rawalpindi"},
    {"store":"khaadi.com","store_name":"Khaadi","title":"Peach Blossom Silk Peshwas","url":"https://khaadi.com/search?q=peach+peshwas","image":"https://images.unsplash.com/photo-1518611012118-696072aa579a?w=500&q=80","price":22000,"silhouette":"ballgown","neckline":"sweetheart","sleeve":"sleeveless","length":"maxi","color":"pink","occasion":"wedding","area":"Rawalpindi","branch":"Bahria Town Phase 7"},
    {"store":"khaadi.com","store_name":"Khaadi","title":"Rose Pink Tailored Bodycon","url":"https://khaadi.com/search?q=bodycon","image":"https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=500&q=80","price":4900,"silhouette":"bodycon","neckline":"round","sleeve":"short","length":"knee","color":"pink","occasion":"party","area":"Islamabad","branch":"Giga Mall, DHA Phase 2"},

    # ── SANA SAFINAZ (sanasafinaz.com) ────────────────────────────────────────
    {"store":"sanasafinaz.com","store_name":"Sana Safinaz","title":"Emerald Silk Festive Gown","url":"https://www.sanasafinaz.com/pk/catalogsearch/result/?q=silk+gown","image":"https://images.unsplash.com/photo-1519764622345-23439dd774f7?w=500&q=80","price":18500,"silhouette":"empire","neckline":"off-shoulder","sleeve":"sleeveless","length":"maxi","color":"green","occasion":"formal","area":"Islamabad","branch":"Centaurus Mall, F-8 Islamabad"},
    {"store":"sanasafinaz.com","store_name":"Sana Safinaz","title":"Turquoise Blue Lawn Kurti","url":"https://www.sanasafinaz.com/pk/catalogsearch/result/?q=turquoise+kurti","image":"https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=500&q=80","price":7800,"silhouette":"straight","neckline":"round","sleeve":"three-quarter","length":"maxi","color":"blue","occasion":"casual","area":"Islamabad","branch":"Beverly Centre, Blue Area"},
    {"store":"sanasafinaz.com","store_name":"Sana Safinaz","title":"Ivory Heavy Bridal Peshwas","url":"https://www.sanasafinaz.com/pk/catalogsearch/result/?q=bridal+peshwas","image":"https://images.unsplash.com/photo-1580227974546-fbd3e95299d4?w=500&q=80","price":38000,"silhouette":"ballgown","neckline":"sweetheart","sleeve":"full","length":"maxi","color":"white","occasion":"wedding","area":"Rawalpindi","branch":"Gulrez Housing Scheme"},

    # ── GUL AHMED (gulahmedshop.com) ─────────────────────────────────────────
    {"store":"gulahmed.com","store_name":"Gul Ahmed","title":"Emerald Green Organza Maxi","url":"https://www.gulahmedshop.com/catalogsearch/result/?q=green+organza+maxi","image":"https://images.unsplash.com/photo-1568252542512-9fe8fe9c87bb?w=500&q=80","price":10500,"silhouette":"a-line","neckline":"v-neck","sleeve":"three-quarter","length":"maxi","color":"green","occasion":"formal","area":"Rawalpindi","branch":"Chandni Chowk, Murree Road"},
    {"store":"gulahmed.com","store_name":"Gul Ahmed","title":"Red Georgette Formal Suit","url":"https://www.gulahmedshop.com/catalogsearch/result/?q=red+formal","image":"https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=500&q=80","price":9800,"silhouette":"a-line","neckline":"square","sleeve":"bell","length":"maxi","color":"red","occasion":"formal","area":"Islamabad","branch":"G-9 Markaz (Karachi Company)"},
    {"store":"gulahmed.com","store_name":"Gul Ahmed","title":"Classic White Cotton Chickenkari","url":"https://www.gulahmedshop.com/catalogsearch/result/?q=white+cotton","image":"https://images.unsplash.com/photo-1585487000160-6ebcfceb0d03?w=500&q=80","price":4900,"silhouette":"wrap","neckline":"v-neck","sleeve":"short","length":"knee","color":"white","occasion":"casual","area":"Islamabad","branch":"F-10 Markaz, Islamabad"},

    # ── J. (JUNAID JAMSHED) (junaidjamshed.com) ──────────────────────────────
    {"store":"jdotpk.com","store_name":"J.","title":"Blush Pink Festive Net Maxi","url":"https://www.junaidjamshed.com/catalogsearch/result/?q=pink+maxi","image":"https://images.unsplash.com/photo-1578450671530-5b6a7d971b37?w=500&q=80","price":12500,"silhouette":"a-line","neckline":"v-neck","sleeve":"cap","length":"maxi","color":"pink","occasion":"wedding","area":"Islamabad","branch":"Centaurus Mall, F-8 Islamabad"},
    {"store":"jdotpk.com","store_name":"J.","title":"Deep Navy Blue Chiffon Tunic","url":"https://www.junaidjamshed.com/catalogsearch/result/?q=navy+tunic","image":"https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=500&q=80","price":6200,"silhouette":"straight","neckline":"boat","sleeve":"three-quarter","length":"midi","color":"blue","occasion":"office","area":"Rawalpindi","branch":"Saddar Cantt, Rawalpindi"},
    {"store":"jdotpk.com","store_name":"J.","title":"Black Velvet Night Dress","url":"https://www.junaidjamshed.com/catalogsearch/result/?q=black+velvet","image":"https://images.unsplash.com/photo-1617922001439-4a2e6562f328?w=500&q=80","price":8900,"silhouette":"bodycon","neckline":"halter","sleeve":"sleeveless","length":"mini","color":"black","occasion":"party","area":"Islamabad","branch":"Giga Mall, DHA Phase 2"},

    # ── NISHAT LINEN (nishatlinen.com) ───────────────────────────────────────
    {"store":"nishatlinen.com","store_name":"Nishat Linen","title":"Emerald Green Luxury Lawn Maxi","url":"https://nishatlinen.com/search?q=green+maxi","image":"https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=500&q=80","price":7900,"silhouette":"a-line","neckline":"round","sleeve":"full","length":"maxi","color":"green","occasion":"casual","area":"Islamabad","branch":"Centaurus Mall, F-8 Islamabad"},
    {"store":"nishatlinen.com","store_name":"Nishat Linen","title":"Beige Linen Straight Shift","url":"https://nishatlinen.com/search?q=beige+linen","image":"https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=500&q=80","price":4500,"silhouette":"shift","neckline":"boat","sleeve":"short","length":"knee","color":"beige","occasion":"casual","area":"Islamabad","branch":"F-7 Markaz, Islamabad"},
    {"store":"nishatlinen.com","store_name":"Nishat Linen","title":"Royal Purple Silk Peshwas","url":"https://nishatlinen.com/search?q=purple+silk","image":"https://images.unsplash.com/photo-1554568218-0f1715e72254?w=500&q=80","price":14500,"silhouette":"ballgown","neckline":"square","sleeve":"bell","length":"maxi","color":"purple","occasion":"formal","area":"Rawalpindi","branch":"Saddar, Rawalpindi"},

    # ── GENERATION (generation.com.pk) ───────────────────────────────────────
    {"store":"generation.com.pk","store_name":"Generation","title":"Green Handcrafted Angrakha Frock","url":"https://generation.com.pk/search?q=green+frock","image":"https://images.unsplash.com/photo-1525507119028-ed4c629a60a3?w=500&q=80","price":6998,"silhouette":"wrap","neckline":"v-neck","sleeve":"full","length":"maxi","color":"green","occasion":"casual","area":"Islamabad","branch":"F-7 Jinnah Super, Islamabad"},
    {"store":"generation.com.pk","store_name":"Generation","title":"Rust Terracotta Midi Shift","url":"https://generation.com.pk/search?q=rust+shift","image":"https://images.unsplash.com/photo-1578450671530-5b6a7d971b37?w=500&q=80","price":4800,"silhouette":"shift","neckline":"round","sleeve":"short","length":"midi","color":"orange","occasion":"casual","area":"Islamabad","branch":"Giga Mall, DHA Phase 2"},

    # ── ETHNIC (ethnic.pk) ───────────────────────────────────────────────────
    {"store":"ethnic.pk","store_name":"Ethnic","title":"Forest Green Raw Silk Gown","url":"https://ethnic.pk/search?q=green+gown","image":"https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=500&q=80","price":11990,"silhouette":"a-line","neckline":"v-neck","sleeve":"full","length":"maxi","color":"green","occasion":"formal","area":"Islamabad","branch":"Centaurus Mall, F-8 Islamabad"},
    {"store":"ethnic.pk","store_name":"Ethnic","title":"Mustard Embroidered A-Line","url":"https://ethnic.pk/search?q=mustard+embroidered","image":"https://images.unsplash.com/photo-1509631179647-0177331693ae?w=500&q=80","price":6500,"silhouette":"a-line","neckline":"round","sleeve":"full","length":"midi","color":"yellow","occasion":"casual","area":"Rawalpindi","branch":"Saddar, Rawalpindi"},

    # ── MARIA.B (mariab.pk) ──────────────────────────────────────────────────
    {"store":"mariab.pk","store_name":"Maria.B","title":"Emerald Velvet Luxury Evening Gown","url":"https://www.mariab.pk/catalogsearch/result/?q=velvet+gown","image":"https://images.unsplash.com/photo-1519764622345-23439dd774f7?w=500&q=80","price":28500,"silhouette":"a-line","neckline":"square","sleeve":"full","length":"maxi","color":"green","occasion":"wedding","area":"Islamabad","branch":"F-7 Markaz, Islamabad"},
    {"store":"mariab.pk","store_name":"Maria.B","title":"Pink Net Embroidered Wedding Peshwas","url":"https://www.mariab.pk/catalogsearch/result/?q=pink+wedding","image":"https://images.unsplash.com/photo-1580227974546-fbd3e95299d4?w=500&q=80","price":34000,"silhouette":"ballgown","neckline":"sweetheart","sleeve":"cap","length":"maxi","color":"pink","occasion":"wedding","area":"Rawalpindi","branch":"Saddar Cantt, Rawalpindi"},

    # ── ALKARAM STUDIO (alkaramstudio.com) ────────────────────────────────────
    {"store":"alkaramstudio.com","store_name":"Alkaram","title":"Mint Green Chiffon Maxi Suit","url":"https://www.alkaramstudio.com/search?q=mint+green","image":"https://images.unsplash.com/photo-1568252542512-9fe8fe9c87bb?w=500&q=80","price":8500,"silhouette":"a-line","neckline":"v-neck","sleeve":"three-quarter","length":"maxi","color":"green","occasion":"formal","area":"Islamabad","branch":"Centaurus Mall, F-8 Islamabad"},
    {"store":"alkaramstudio.com","store_name":"Alkaram","title":"Black Digital Print Satin Shirt","url":"https://www.alkaramstudio.com/search?q=black+satin","image":"https://images.unsplash.com/photo-1551803091-e20673f15770?w=500&q=80","price":4200,"silhouette":"straight","neckline":"round","sleeve":"full","length":"knee","color":"black","occasion":"casual","area":"Rawalpindi","branch":"Commercial Market, Rawalpindi"},

    # ── BONANZA SATRANGI (bonanzasatrangi.com) ────────────────────────────────
    {"store":"bonanzasatrangi.com","store_name":"Bonanza","title":"Emerald Festive Silk Frock","url":"https://bonanzasatrangi.com/search?q=silk+frock","image":"https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=500&q=80","price":9200,"silhouette":"a-line","neckline":"v-neck","sleeve":"full","length":"maxi","color":"green","occasion":"formal","area":"Islamabad","branch":"Jinnah Super, F-7 Islamabad"},
    {"store":"bonanzasatrangi.com","store_name":"Bonanza","title":"Multi Floral Printed Lawn Wrap","url":"https://bonanzasatrangi.com/search?q=floral+wrap","image":"https://images.unsplash.com/photo-1601924994987-69e26d50dc26?w=500&q=80","price":4900,"silhouette":"wrap","neckline":"v-neck","sleeve":"three-quarter","length":"midi","color":"multi","occasion":"casual","area":"Rawalpindi","branch":"Bahria Town Phase 4"}
]

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    conn.executescript(SCHEMA)
    
    # Check count
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count < len(EXPANDED_PRODUCTS):
        print(f"[db] Upgrading database with {len(EXPANDED_PRODUCTS)} extensive multi-store items...")
        conn.execute("DELETE FROM products")
        for p in EXPANDED_PRODUCTS:
            conn.execute("""
                INSERT INTO products (store, store_name, title, url, image, price, currency, silhouette, neckline, sleeve, length, color, occasion, area, branch)
                VALUES (:store, :store_name, :title, :url, :image, :price, 'PKR', :silhouette, :neckline, :sleeve, :length, :color, :occasion, :area, :branch)
            """, p)
        conn.commit()
        print(f"[db] Database updated with {len(EXPANDED_PRODUCTS)} products.")
    conn.close()

def load_all_products() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return [dict(r) for r in rows]
