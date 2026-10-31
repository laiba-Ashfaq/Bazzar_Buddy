# BAZAAR BUDDY— Autonomous Fashion Search Engine

A sketch-to-shop visual search engine for apparel stores across the Twin Cities (Islamabad & Rawalpindi).

---

## 1. What APIs & Agent Keys You Need

| Service | Why Needed | How to Get (Free) |
|---|---|---|
| **Google Gemini API** (Primary Vision Agent) | Analyzes uploaded sketches/photos and extracts 6 attributes (`silhouette`, `neckline`, `sleeve`, `length`, `color`, `occasion`). | 1. Visit [aistudio.google.com](https://aistudio.google.com/app/apikey)<br>2. Click **"Get API key"** (Free tier)<br>3. Copy key into `.env` |
| **Ollama / Gemma 3** (Optional Local Fallback) | Run 100% offline vision model with zero rate-limits. | 1. Download [ollama.com](https://ollama.com)<br>2. Run in terminal: `ollama run llava:7b` |

*Note: The frontend also includes a standalone instant inference engine, so you can test and present the full MVP even without an active internet connection or API key.*

---

## 2. Project Architecture

```
Ai Stylist/
├── index.html                 # Vyzor-styled responsive Frontend (Sky Blue & Lime theme)
├── .env.example               # Template for API keys
├── backend/
│   ├── main.py                # FastAPI endpoints (/health, /extract, /search)
│   ├── ai.py                  # Gemini Vision + Ollama fallback pipeline
│   ├── scoring.py             # Near-miss style graph & attribute weighting
│   ├── db.py                  # SQLite product database & store loader
│   ├── schema.py              # Pydantic data contract
│   └── data/
│       ├── products.db        # SQLite database with 60+ dresses
│       ├── stores.json        # Verified Twin Cities store branches (Centaurus, F-7, Saddar)
│       └── similarity.json    # Style graph similarity & conflict weights
└── scraper/
    ├── scrape_shopify.py      # Shopify products.json catalog scraper
    └── tag_products.py        # Automatic attribute tagging pipeline
```

---

## 3. How to Run the Project (Step-by-Step)

### Step 1: Open the Frontend MVP (Immediate)
Simply double-click `index.html` in your file explorer or open it in Chrome / Edge / Firefox.
- **Working File Upload**: Drag and drop any dress sketch or click to select a file.
- **Pre-loaded Samples**: Click any of the 3 quick demo buttons (*Emerald Maxi*, *Ivory Fit&Flare*, *Black Velvet*).
- **Interactive Attribute Chips**: Edit any dropdown (Silhouette, Sleeve, Neckline, etc.) — the match scores update in real time.
- **Real Working Store Links**: Click **"Visit Store"** on any card to open the live search on Khaadi, Sana Safinaz, Gul Ahmed, or J. in a new tab.
- **Twin Cities Filters**: Filter by budget (PKR slider) and area (Islamabad, Rawalpindi, Online).
- **Dark/Light Mode**: Toggle the moon/sun icon in the top right.

---

### Step 2: Set Up Backend & Gemini Vision API

1. Open PowerShell / Command Prompt in `Ai Stylist/`:
   ```bash
   # Copy environment template
   copy .env.example .env
   ```

2. Open `.env` and paste your Gemini key:
   ```env
   GEMINI_API_KEY=AIzaSy...your_real_key_here
   GEMINI_MODEL=gemini-1.5-flash
   ```

3. Run the FastAPI Backend:
   ```bash
   cd backend
   python -m uvicorn main:app --reload --port 8000
   ```
   - Auto-generated Swagger API docs will be live at: **`http://localhost:8000/docs`**
   - Health check: **`http://localhost:8000/health`**

---

### Step 3: Run the Real Store Scraper

To scrape live products from Pakistani fashion brands:
```bash
# Scrape Khaadi
python scraper/scrape_shopify.py khaadi.com

# Scrape Sana Safinaz
python scraper/scrape_shopify.py sanasafinaz.com

# Scrape Gul Ahmed
python scraper/scrape_shopify.py gulahmedshop.com
```
Scraped JSON files are saved into `scraper/raw/`.

To auto-tag the scraped products and insert them into the search database:
```bash
python scraper/tag_products.py
```

---

## 4. How to Verify & Test Core Functionality

Run these terminal commands to verify every layer:

### 1. Test Database & Store Loading:
```bash
python -c "import sys; sys.path.append('backend'); import db; db.init_db(); print('Products:', len(db.load_all_products()))"
```
*(Returns 60 items seeded and ready)*

### 2. Test Near-Miss Graph Scoring:
```bash
python -c "import sys; sys.path.append('backend'); import scoring; s, m, d = scoring.score({'silhouette':'a-line','neckline':'v-neck','sleeve':'full','length':'maxi','color':'green','occasion':'formal'}, {'silhouette':'a-line','neckline':'v-neck','sleeve':'three-quarter','length':'maxi','color':'green','occasion':'formal'}); print('Score:', s, 'Matched:', m, 'Differs:', d)"
```
*(Demonstrates 95.5% match where sleeve is recognized as near-miss similar rather than exact failure)*

### 3. Test API Health Endpoint:
Open your browser or run:
```bash
curl http://localhost:8000/health
```
*(Returns `{"status":"ok", "products_loaded":60}`)*
