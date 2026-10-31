"""
db.py — SQLite helpers: init, seed with mock data, load all products
"""
import json
import sqlite3
from pathlib import Path

DB_PATH    = Path(__file__).parent / "data" / "products.db"
STORES_PATH = Path(__file__).parent / "data" / "stores.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    store     TEXT NOT NULL,
    title     TEXT NOT NULL,
    url       TEXT NOT NULL,
    image     TEXT,
    price     REAL DEFAULT 0,
    currency  TEXT DEFAULT 'PKR',
    silhouette TEXT DEFAULT 'unknown',
    neckline   TEXT DEFAULT 'unknown',
    sleeve     TEXT DEFAULT 'unknown',
    length     TEXT DEFAULT 'unknown',
    color      TEXT DEFAULT 'unknown',
    occasion   TEXT DEFAULT 'unknown'
);
"""

# ── 60 realistic mock products for Twin Cities stores ─────────────────────────
MOCK_PRODUCTS = [
    # ── Khaadi-style store ───────────────────────────────────────────────────
    {"store":"khaadi.com","title":"Emerald Chiffon Maxi","url":"https://khaadi.com/products/emerald-maxi","image":"https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400","price":8900,"silhouette":"a-line","neckline":"v-neck","sleeve":"full","length":"maxi","color":"green","occasion":"formal"},
    {"store":"khaadi.com","title":"Ivory Lace Fit & Flare","url":"https://khaadi.com/products/ivory-lace","image":"https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=400","price":12500,"silhouette":"fit-and-flare","neckline":"sweetheart","sleeve":"sleeveless","length":"knee","color":"white","occasion":"wedding"},
    {"store":"khaadi.com","title":"Navy Midi Wrap Dress","url":"https://khaadi.com/products/navy-wrap","image":"https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=400","price":6500,"silhouette":"wrap","neckline":"v-neck","sleeve":"three-quarter","length":"midi","color":"blue","occasion":"office"},
    {"store":"khaadi.com","title":"Rose Pink Bodycon","url":"https://khaadi.com/products/rose-bodycon","image":"https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=400","price":4900,"silhouette":"bodycon","neckline":"round","sleeve":"short","length":"knee","color":"pink","occasion":"party"},
    {"store":"khaadi.com","title":"Sage Green Shift Dress","url":"https://khaadi.com/products/sage-shift","image":"https://images.unsplash.com/photo-1502716119720-b23a93e5fe1b?w=400","price":5500,"silhouette":"shift","neckline":"boat","sleeve":"sleeveless","length":"knee","color":"green","occasion":"casual"},
    {"store":"khaadi.com","title":"Black Embroidered Maxi","url":"https://khaadi.com/products/black-embroidered","image":"https://images.unsplash.com/photo-1583744946564-b52ac1c389c8?w=400","price":15000,"silhouette":"a-line","neckline":"high-neck","sleeve":"full","length":"maxi","color":"black","occasion":"formal"},
    {"store":"khaadi.com","title":"Peach Ballgown Dress","url":"https://khaadi.com/products/peach-ballgown","image":"https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400","price":22000,"silhouette":"ballgown","neckline":"sweetheart","sleeve":"sleeveless","length":"maxi","color":"pink","occasion":"wedding"},
    {"store":"khaadi.com","title":"Mustard Printed Midi","url":"https://khaadi.com/products/mustard-midi","image":"https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400","price":7200,"silhouette":"a-line","neckline":"round","sleeve":"puff","length":"midi","color":"yellow","occasion":"casual"},
    {"store":"khaadi.com","title":"Grey Straight Cut","url":"https://khaadi.com/products/grey-straight","image":"https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=400","price":5800,"silhouette":"straight","neckline":"v-neck","sleeve":"full","length":"midi","color":"grey","occasion":"office"},
    {"store":"khaadi.com","title":"Burgundy Empire Waist","url":"https://khaadi.com/products/burgundy-empire","image":"https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=400","price":9500,"silhouette":"empire","neckline":"square","sleeve":"bell","length":"maxi","color":"red","occasion":"formal"},
    # ── Sana Safinaz style ───────────────────────────────────────────────────
    {"store":"sanasafinaz.com","title":"Turquoise Lawn Maxi","url":"https://sanasafinaz.com/products/turquoise-lawn","image":"https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400","price":7800,"silhouette":"straight","neckline":"round","sleeve":"three-quarter","length":"maxi","color":"blue","occasion":"casual"},
    {"store":"sanasafinaz.com","title":"Coral Off-Shoulder Midi","url":"https://sanasafinaz.com/products/coral-off-shoulder","image":"https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=400","price":11000,"silhouette":"fit-and-flare","neckline":"off-shoulder","sleeve":"sleeveless","length":"midi","color":"orange","occasion":"party"},
    {"store":"sanasafinaz.com","title":"Ivory Embroidered Maxi","url":"https://sanasafinaz.com/products/ivory-embroidered","image":"https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=400","price":18000,"silhouette":"a-line","neckline":"v-neck","sleeve":"full","length":"maxi","color":"white","occasion":"wedding"},
    {"store":"sanasafinaz.com","title":"Teal Formal Shift","url":"https://sanasafinaz.com/products/teal-formal","image":"https://images.unsplash.com/photo-1601924994987-69e26d50dc26?w=400","price":8200,"silhouette":"shift","neckline":"square","sleeve":"cap","length":"knee","color":"blue","occasion":"office"},
    {"store":"sanasafinaz.com","title":"Pink Puff Sleeve Mini","url":"https://sanasafinaz.com/products/pink-puff-mini","image":"https://images.unsplash.com/photo-1545291730-faff8ca1d4b0?w=400","price":6300,"silhouette":"a-line","neckline":"sweetheart","sleeve":"puff","length":"mini","color":"pink","occasion":"party"},
    {"store":"sanasafinaz.com","title":"Black Halter Bodycon","url":"https://sanasafinaz.com/products/black-halter","image":"https://images.unsplash.com/photo-1470259078422-826894b933aa?w=400","price":5900,"silhouette":"bodycon","neckline":"halter","sleeve":"sleeveless","length":"knee","color":"black","occasion":"party"},
    {"store":"sanasafinaz.com","title":"Olive Wrap Maxi","url":"https://sanasafinaz.com/products/olive-wrap","image":"https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400","price":9200,"silhouette":"wrap","neckline":"v-neck","sleeve":"full","length":"maxi","color":"green","occasion":"casual"},
    {"store":"sanasafinaz.com","title":"White Lace Ballgown","url":"https://sanasafinaz.com/products/white-lace-ball","image":"https://images.unsplash.com/photo-1580227974546-fbd3e95299d4?w=400","price":35000,"silhouette":"ballgown","neckline":"sweetheart","sleeve":"cap","length":"maxi","color":"white","occasion":"wedding"},
    {"store":"sanasafinaz.com","title":"Lavender Bell Sleeve","url":"https://sanasafinaz.com/products/lavender-bell","image":"https://images.unsplash.com/photo-1554568218-0f1715e72254?w=400","price":7600,"silhouette":"a-line","neckline":"round","sleeve":"bell","length":"midi","color":"purple","occasion":"casual"},
    {"store":"sanasafinaz.com","title":"Beige Linen Shift","url":"https://sanasafinaz.com/products/beige-linen","image":"https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400","price":5200,"silhouette":"shift","neckline":"boat","sleeve":"short","length":"knee","color":"beige","occasion":"office"},
    # ── Gul Ahmed style ──────────────────────────────────────────────────────
    {"store":"gulahmed.com","title":"Red Georgette Maxi","url":"https://gulahmed.com/products/red-georgette","image":"https://images.unsplash.com/photo-1568252542512-9fe8fe9c87bb?w=400","price":10500,"silhouette":"a-line","neckline":"v-neck","sleeve":"three-quarter","length":"maxi","color":"red","occasion":"formal"},
    {"store":"gulahmed.com","title":"Blue Printed Kurta Maxi","url":"https://gulahmed.com/products/blue-printed","image":"https://images.unsplash.com/photo-1525507119028-ed4c629a60a3?w=400","price":4500,"silhouette":"straight","neckline":"round","sleeve":"full","length":"maxi","color":"blue","occasion":"casual"},
    {"store":"gulahmed.com","title":"Green Satin Empire","url":"https://gulahmed.com/products/green-satin","image":"https://images.unsplash.com/photo-1519764622345-23439dd774f7?w=400","price":13000,"silhouette":"empire","neckline":"off-shoulder","sleeve":"sleeveless","length":"maxi","color":"green","occasion":"formal"},
    {"store":"gulahmed.com","title":"Black Party Bodycon","url":"https://gulahmed.com/products/black-party","image":"https://images.unsplash.com/photo-1551803091-e20673f15770?w=400","price":5500,"silhouette":"bodycon","neckline":"high-neck","sleeve":"sleeveless","length":"mini","color":"black","occasion":"party"},
    {"store":"gulahmed.com","title":"White Cotton Wrap","url":"https://gulahmed.com/products/white-wrap","image":"https://images.unsplash.com/photo-1585487000160-6ebcfceb0d03?w=400","price":3900,"silhouette":"wrap","neckline":"v-neck","sleeve":"short","length":"knee","color":"white","occasion":"casual"},
    {"store":"gulahmed.com","title":"Pink Floral A-Line Midi","url":"https://gulahmed.com/products/pink-floral","image":"https://images.unsplash.com/photo-1512436991641-6745cdb1723f?w=400","price":6800,"silhouette":"a-line","neckline":"sweetheart","sleeve":"puff","length":"midi","color":"pink","occasion":"casual"},
    {"store":"gulahmed.com","title":"Purple Formal Maxi","url":"https://gulahmed.com/products/purple-formal","image":"https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=400","price":9800,"silhouette":"a-line","neckline":"square","sleeve":"bell","length":"maxi","color":"purple","occasion":"formal"},
    {"store":"gulahmed.com","title":"Beige Kaftan Style","url":"https://gulahmed.com/products/beige-kaftan","image":"https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400","price":7200,"silhouette":"straight","neckline":"round","sleeve":"full","length":"maxi","color":"beige","occasion":"casual"},
    {"store":"gulahmed.com","title":"Maroon Wedding Maxi","url":"https://gulahmed.com/products/maroon-wedding","image":"https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400","price":24000,"silhouette":"ballgown","neckline":"sweetheart","sleeve":"full","length":"maxi","color":"red","occasion":"wedding"},
    {"store":"gulahmed.com","title":"Grey Office Shift","url":"https://gulahmed.com/products/grey-shift","image":"https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=400","price":4800,"silhouette":"shift","neckline":"high-neck","sleeve":"three-quarter","length":"knee","color":"grey","occasion":"office"},
    # ── J. / Junaid Jamshed style ────────────────────────────────────────────
    {"store":"jdotpk.com","title":"Blush Pink Chiffon Maxi","url":"https://jdotpk.com/products/blush-maxi","image":"https://images.unsplash.com/photo-1578450671530-5b6a7d971b37?w=400","price":11500,"silhouette":"a-line","neckline":"v-neck","sleeve":"cap","length":"maxi","color":"pink","occasion":"wedding"},
    {"store":"jdotpk.com","title":"Navy Blue Office Dress","url":"https://jdotpk.com/products/navy-office","image":"https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=400","price":6200,"silhouette":"straight","neckline":"boat","sleeve":"three-quarter","length":"midi","color":"blue","occasion":"office"},
    {"store":"jdotpk.com","title":"Black Velvet Bodycon","url":"https://jdotpk.com/products/black-velvet","image":"https://images.unsplash.com/photo-1617922001439-4a2e6562f328?w=400","price":8900,"silhouette":"bodycon","neckline":"halter","sleeve":"sleeveless","length":"mini","color":"black","occasion":"party"},
    {"store":"jdotpk.com","title":"Mustard Wrap Midi","url":"https://jdotpk.com/products/mustard-wrap","image":"https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400","price":7100,"silhouette":"wrap","neckline":"v-neck","sleeve":"full","length":"midi","color":"yellow","occasion":"casual"},
    {"store":"jdotpk.com","title":"Teal Embroidered Formal","url":"https://jdotpk.com/products/teal-formal","image":"https://images.unsplash.com/photo-1542295669297-4d352b042bca?w=400","price":14000,"silhouette":"a-line","neckline":"square","sleeve":"full","length":"maxi","color":"blue","occasion":"formal"},
    {"store":"jdotpk.com","title":"White Summer Fit & Flare","url":"https://jdotpk.com/products/white-summer","image":"https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400","price":5600,"silhouette":"fit-and-flare","neckline":"off-shoulder","sleeve":"sleeveless","length":"midi","color":"white","occasion":"casual"},
    {"store":"jdotpk.com","title":"Purple Bell Sleeve Maxi","url":"https://jdotpk.com/products/purple-bell","image":"https://images.unsplash.com/photo-1554568218-0f1715e72254?w=400","price":9300,"silhouette":"a-line","neckline":"round","sleeve":"bell","length":"maxi","color":"purple","occasion":"formal"},
    {"store":"jdotpk.com","title":"Sage Green Empire","url":"https://jdotpk.com/products/sage-empire","image":"https://images.unsplash.com/photo-1502716119720-b23a93e5fe1b?w=400","price":10200,"silhouette":"empire","neckline":"sweetheart","sleeve":"puff","length":"maxi","color":"green","occasion":"wedding"},
    {"store":"jdotpk.com","title":"Brown Casual Shift","url":"https://jdotpk.com/products/brown-shift","image":"https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400","price":4200,"silhouette":"shift","neckline":"round","sleeve":"short","length":"knee","color":"brown","occasion":"casual"},
    {"store":"jdotpk.com","title":"Red Party Mini","url":"https://jdotpk.com/products/red-mini","image":"https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=400","price":5100,"silhouette":"a-line","neckline":"v-neck","sleeve":"sleeveless","length":"mini","color":"red","occasion":"party"},
    # ── Zara Pakistan online ─────────────────────────────────────────────────
    {"store":"zara-pk.online","title":"Black Minimal Maxi","url":"https://zara-pk.online/products/black-minimal","image":"https://images.unsplash.com/photo-1583744946564-b52ac1c389c8?w=400","price":16000,"silhouette":"straight","neckline":"high-neck","sleeve":"full","length":"maxi","color":"black","occasion":"formal"},
    {"store":"zara-pk.online","title":"White Shirt Dress Midi","url":"https://zara-pk.online/products/white-shirt","image":"https://images.unsplash.com/photo-1585487000160-6ebcfceb0d03?w=400","price":11500,"silhouette":"straight","neckline":"v-neck","sleeve":"full","length":"midi","color":"white","occasion":"office"},
    {"store":"zara-pk.online","title":"Beige Trench Dress","url":"https://zara-pk.online/products/beige-trench","image":"https://images.unsplash.com/photo-1520975954732-35dd22299614?w=400","price":19000,"silhouette":"wrap","neckline":"v-neck","sleeve":"full","length":"midi","color":"beige","occasion":"office"},
    {"store":"zara-pk.online","title":"Red Off-Shoulder Mini","url":"https://zara-pk.online/products/red-off-shoulder","image":"https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=400","price":13000,"silhouette":"bodycon","neckline":"off-shoulder","sleeve":"sleeveless","length":"mini","color":"red","occasion":"party"},
    {"store":"zara-pk.online","title":"Navy Midi Skater","url":"https://zara-pk.online/products/navy-skater","image":"https://images.unsplash.com/photo-1568252542512-9fe8fe9c87bb?w=400","price":12000,"silhouette":"fit-and-flare","neckline":"square","sleeve":"short","length":"midi","color":"blue","occasion":"casual"},
    {"store":"zara-pk.online","title":"Green Satin Slip Maxi","url":"https://zara-pk.online/products/green-slip","image":"https://images.unsplash.com/photo-1519764622345-23439dd774f7?w=400","price":18500,"silhouette":"straight","neckline":"v-neck","sleeve":"sleeveless","length":"maxi","color":"green","occasion":"formal"},
    {"store":"zara-pk.online","title":"Pink Balloon Dress","url":"https://zara-pk.online/products/pink-balloon","image":"https://images.unsplash.com/photo-1512436991641-6745cdb1723f?w=400","price":15000,"silhouette":"empire","neckline":"round","sleeve":"puff","length":"midi","color":"pink","occasion":"party"},
    {"store":"zara-pk.online","title":"Camel Coat Dress","url":"https://zara-pk.online/products/camel-coat","image":"https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=400","price":22000,"silhouette":"straight","neckline":"v-neck","sleeve":"full","length":"midi","color":"beige","occasion":"office"},
    {"store":"zara-pk.online","title":"Purple Floral Maxi","url":"https://zara-pk.online/products/purple-floral","image":"https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400","price":14500,"silhouette":"a-line","neckline":"halter","sleeve":"sleeveless","length":"maxi","color":"purple","occasion":"casual"},
    {"store":"zara-pk.online","title":"Grey Blazer Dress","url":"https://zara-pk.online/products/grey-blazer","image":"https://images.unsplash.com/photo-1551803091-e20673f15770?w=400","price":21000,"silhouette":"straight","neckline":"v-neck","sleeve":"three-quarter","length":"knee","color":"grey","occasion":"office"},
    # ── Bonanza Satrangi ─────────────────────────────────────────────────────
    {"store":"bonanzasatrangi.com","title":"Multi Printed Wrap","url":"https://bonanzasatrangi.com/products/multi-wrap","image":"https://images.unsplash.com/photo-1601924994987-69e26d50dc26?w=400","price":4900,"silhouette":"wrap","neckline":"v-neck","sleeve":"three-quarter","length":"midi","color":"multi","occasion":"casual"},
    {"store":"bonanzasatrangi.com","title":"Orange Casual Shift","url":"https://bonanzasatrangi.com/products/orange-shift","image":"https://images.unsplash.com/photo-1578450671530-5b6a7d971b37?w=400","price":3800,"silhouette":"shift","neckline":"round","sleeve":"short","length":"knee","color":"orange","occasion":"casual"},
    {"store":"bonanzasatrangi.com","title":"Yellow Floral Maxi","url":"https://bonanzasatrangi.com/products/yellow-floral","image":"https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400","price":5600,"silhouette":"a-line","neckline":"round","sleeve":"full","length":"maxi","color":"yellow","occasion":"casual"},
    {"store":"bonanzasatrangi.com","title":"Black Formal Bodycon","url":"https://bonanzasatrangi.com/products/black-bodycon","image":"https://images.unsplash.com/photo-1470259078422-826894b933aa?w=400","price":4200,"silhouette":"bodycon","neckline":"v-neck","sleeve":"sleeveless","length":"knee","color":"black","occasion":"formal"},
    {"store":"bonanzasatrangi.com","title":"Pink Kurta Maxi","url":"https://bonanzasatrangi.com/products/pink-kurta","image":"https://images.unsplash.com/photo-1567401893414-76b7b1e5a7a5?w=400","price":3500,"silhouette":"straight","neckline":"round","sleeve":"full","length":"maxi","color":"pink","occasion":"casual"},
    {"store":"bonanzasatrangi.com","title":"Blue Party Dress","url":"https://bonanzasatrangi.com/products/blue-party","image":"https://images.unsplash.com/photo-1568252542512-9fe8fe9c87bb?w=400","price":6100,"silhouette":"fit-and-flare","neckline":"halter","sleeve":"sleeveless","length":"midi","color":"blue","occasion":"party"},
    {"store":"bonanzasatrangi.com","title":"Beige Embroidered Maxi","url":"https://bonanzasatrangi.com/products/beige-embroidered","image":"https://images.unsplash.com/photo-1502716119720-b23a93e5fe1b?w=400","price":7800,"silhouette":"a-line","neckline":"square","sleeve":"full","length":"maxi","color":"beige","occasion":"formal"},
    {"store":"bonanzasatrangi.com","title":"Red Festive Ballgown","url":"https://bonanzasatrangi.com/products/red-festive","image":"https://images.unsplash.com/photo-1580227974546-fbd3e95299d4?w=400","price":19500,"silhouette":"ballgown","neckline":"sweetheart","sleeve":"cap","length":"maxi","color":"red","occasion":"wedding"},
    {"store":"bonanzasatrangi.com","title":"Green Lawn Kurta","url":"https://bonanzasatrangi.com/products/green-kurta","image":"https://images.unsplash.com/photo-1525507119028-ed4c629a60a3?w=400","price":2900,"silhouette":"straight","neckline":"round","sleeve":"full","length":"maxi","color":"green","occasion":"casual"},
    {"store":"bonanzasatrangi.com","title":"Purple Party Mini","url":"https://bonanzasatrangi.com/products/purple-mini","image":"https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=400","price":5300,"silhouette":"a-line","neckline":"off-shoulder","sleeve":"puff","length":"mini","color":"purple","occasion":"party"},
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create table and seed if empty."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    conn.executescript(SCHEMA)
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        print(f"[db] Seeding {len(MOCK_PRODUCTS)} mock products...")
        conn.executemany(
            """INSERT INTO products
               (store,title,url,image,price,silhouette,neckline,sleeve,length,color,occasion)
               VALUES (:store,:title,:url,:image,:price,
                       :silhouette,:neckline,:sleeve,:length,:color,:occasion)""",
            MOCK_PRODUCTS,
        )
        conn.commit()
        print("[db] Seed complete.")
    else:
        print(f"[db] {count} products already in DB.")
    conn.close()


def load_all_products() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_product(p: dict) -> int:
    conn = get_connection()
    cur = conn.execute(
        """INSERT OR IGNORE INTO products
           (store,title,url,image,price,silhouette,neckline,sleeve,length,color,occasion)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (p.get("store"), p.get("title"), p.get("url"), p.get("image"),
         p.get("price", 0), p.get("silhouette", "unknown"),
         p.get("neckline", "unknown"), p.get("sleeve", "unknown"),
         p.get("length", "unknown"), p.get("color", "unknown"),
         p.get("occasion", "unknown")),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id
