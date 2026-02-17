import json
import traceback
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates

from ai.src.predict import predict
from ai.src.dto import build_prediction_dto
from ai.src.market_cap import get_supported
from ai.src.repository.db import get_connection


# =====================
# App
# =====================

app = FastAPI(title="Crypto AI Prediction API")

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "ai" / "data" / "cache"
LOG_DIR = BASE_DIR / "logs"

templates = Jinja2Templates(
    directory=str(BASE_DIR / "api" / "templates")
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "api" / "static"),
    name="static",
)


# =====================
# SEO helper
# =====================

def seo_context(
    *,
    title,
    description,
    keywords,
    canonical,
    og_image="https://cryptoaipredict.com/static/ogp.png",
):
    return {
        "title": title,
        "description": description,
        "keywords": keywords,
        "canonical": canonical,
        "og_image": og_image,
    }


# =====================
# Health Check
# =====================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat()
    }

# =====================
# INDEX (的中率ランキング + 市場データ統合)
# =====================

@app.get("/", response_class=HTMLResponse)
def index(request: Request):

    interval = "1h"
    sort = request.query_params.get("sort")

    path = CACHE_DIR / f"market_overview_{interval}.json"
    coins = []
    generated_at = None 

    # --- 🔥 的中率ランキングを取得するロジック (Prediction仕様に修正) ---
    accuracy_ranking = []
    
    # 1. 基準となる「サポート銘柄リスト」を先に取得
    supported = get_supported(interval)
    # 検索を高速化するためにシンボルをキーにした辞書を作成
    supported_map = {c["symbol"]: c for c in supported}

    try:
        conn = get_connection()
        with conn.cursor(dictionary=True) as cur:
            # フィルタリングに備え、LIMITを少し多めに設定して取得
            cur.execute("""
                SELECT 
                    symbol, 
                    accuracy, 
                    count
                FROM accuracy_ranking
                WHERE count >= 5
                ORDER BY accuracy DESC, count DESC
                LIMIT 50
            """)
            rows = cur.fetchall()
            
            for r in rows:
                full_symbol = r['symbol']
                # 2. Predictionページでサポートされている（Binance上場+Top200）銘柄のみ採用
                if full_symbol in supported_map:
                    coin_info = supported_map[full_symbol]
                    accuracy_ranking.append({
                        "symbol": full_symbol.replace("USDT", ""), # 表示用 (例: BTC)
                        "full_symbol": full_symbol,                 # 内部用
                        "accuracy": r['accuracy'],
                        "count": r['count'],
                        "image": coin_info.get("image") or ""      # 正しい画像URLをセット
                    })
                
                # 上位10件に達したら終了
                if len(accuracy_ranking) >= 10:
                    break
        conn.close()
    except Exception as e:
        print("ACCURACY RANKING LOAD ERROR:", e)

    # symbol_order の作成 (既存ロジック継続)
    symbol_order = {c["symbol"]: i for i, c in enumerate(supported)}

    if path.exists():
        try:
            data = json.loads(path.read_text())
            generated_at = data.get("meta", {}).get("generated_at")
            items = data.get("items", [])

            for item in items:
                data_block = item.get("data") or {}
                metrics = data_block.get("metrics") or {}
                prices = data_block.get("prices") or {}
                meta = item.get("meta") or {}

                past = prices.get("past") or []
                if not past: continue

                symbol_full = meta.get("symbol") or data_block.get("symbol") or ""
                base_symbol = symbol_full.replace("USDT", "")

                current_price = float(metrics.get("current", past[-1]))
                predicted_price = float(metrics.get("predicted", current_price))
                diff = float(metrics.get("diff", 0))
                pct_change = float(metrics.get("pct_change", 0))

                coins.append({
                    "name": base_symbol,
                    "symbol": symbol_full,
                    "image": item.get("image") or "",
                    "current_price": current_price,
                    "predicted_price": predicted_price,
                    "change": diff,
                    "change_percent": pct_change,
                    "trend": [float(x) for x in past[-30:]]
                })
        except Exception as e:
            print("INDEX LOAD ERROR:", e)

    if sort == "change_desc":
        coins.sort(key=lambda x: x["change_percent"], reverse=True)
    elif sort == "change_asc":
        coins.sort(key=lambda x: x["change_percent"])
    elif sort == "marketcap_asc":
        coins.sort(key=lambda x: symbol_order.get(x["symbol"], 9999), reverse=True)
    else:
        coins.sort(key=lambda x: symbol_order.get(x["symbol"], 9999))
        sort = "marketcap_desc"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "coins": coins,
            "current_sort": sort,
            "last_updated": generated_at,
            "accuracy_ranking": accuracy_ranking,
            **seo_context(
                title="Crypto AI Prediction",
                description="Crypto AI Prediction platform",
                keywords="crypto ai prediction",
                canonical="https://cryptoaipredict.com/",
            ),
        },
    )

# =====================
# Other Pages (変更なし)
# =====================

@app.get("/prediction", response_class=HTMLResponse)
def prediction_page(request: Request, symbol: str = Query(None)):
    return templates.TemplateResponse(
        "prediction.html",
        {
            "request": request,
            "initial_symbol": symbol or "",
            **seo_context(title="Prediction | Crypto AI", description="AI crypto price prediction", keywords="crypto prediction ai", canonical="https://cryptoaipredict.com/prediction"),
        },
    )

@app.get("/visualize", response_class=HTMLResponse)
def visualize_page(request: Request):
    return templates.TemplateResponse(
        "visualize.html",
        {
            "request": request,
            **seo_context(title="Market Overview | Crypto AI", description="AI-powered crypto market overview", keywords="crypto market ranking", canonical="https://cryptoaipredict.com/visualize"),
        },
    )

@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, **seo_context(title="About", description="About Crypto AI", keywords="about", canonical="https://cryptoaipredict.com/about")})

@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request, **seo_context(title="Privacy Policy", description="Privacy Policy", keywords="privacy", canonical="https://cryptoaipredict.com/privacy")})

@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request, **seo_context(title="Terms of Service", description="Terms", keywords="terms", canonical="https://cryptoaipredict.com/terms")})

@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request, **seo_context(title="Contact", description="Contact", keywords="contact", canonical="https://cryptoaipredict.com/contact")})

# =====================
# API Endpoints (変更なし)
# =====================

@app.get("/predict")
def api_predict(symbol: str = Query(...), interval: str = Query("1h"), horizon: int = Query(1, ge=1, le=30)):
    try:
        result = predict(symbol, interval, horizon)
        if result.get("status") != "ok": return result
        dto = build_prediction_dto(result)
        return {"meta": {"symbol": dto["symbol"], "interval": dto["meta"]["interval"], "timezone": "UTC", "last_update": int(datetime.now(timezone.utc).timestamp() * 1000)}, "data": dto}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": str(e), "traceback": traceback.format_exc()})

@app.get("/symbols")
def api_symbols(interval: str = Query("1h")):
    try: return get_supported(interval)
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/market-overview")
def api_market_overview(interval: str = Query("1h"), limit: int = Query(20, ge=1, le=200)):
    path = CACHE_DIR / f"market_overview_{interval}.json"
    if not path.exists(): return JSONResponse(status_code=503, content={"error": "Market overview cache not ready"})
    try:
        data = json.loads(path.read_text())
        return {"items": data.get("items", [])[:limit], "meta": data.get("meta", {})}
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/accuracy")
def get_accuracy(symbol: str = Query(...), interval: str = Query("1h")):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    full_symbol = symbol if "USDT" in symbol else symbol + "USDT"
    try:
        cur.execute("""
            SELECT AVG(ABS(predicted_price - actual_price) / base_price) * 100 AS mae_val
            FROM predictions WHERE symbol = %s AND evaluated = 1
        """, (full_symbol,))
        mae_row = cur.fetchone()
        mae = round(mae_row['mae_val'], 2) if mae_row and mae_row['mae_val'] is not None else 0.00
        cur.execute("SELECT accuracy, count FROM accuracy_ranking WHERE symbol = %s OR symbol = %s LIMIT 1", (symbol, full_symbol))
        row = cur.fetchone()
        if not row: return {"status": "ok", "accuracy": 0, "mae": mae, "total": 0}
        return {"status": "ok", "accuracy": row['accuracy'], "mae": mae, "total": row['count']}
    except Exception as e:
        print(f"Accuracy API Error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()
        conn.close()

@app.get("/sitemap.xml", include_in_schema=False)
def dynamic_sitemap():
    base_url = "https://cryptoaipredict.com"
    urls = []
    for route in app.routes:
        if hasattr(route, "path"):
            path = route.path
            if path.startswith(("/api", "/static", "/health", "/docs", "/redoc", "/openapi")) or path in ["/predict", "/symbols", "/accuracy", "/sitemap.xml"] or "{" in path: continue
            urls.append(f"{base_url}{path}")
    try:
        for coin in get_supported("1h"):
            if coin.get("symbol"): urls.append(f"{base_url}/prediction?symbol={coin.get('symbol')}")
    except: pass
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    xml_items = "".join([f"<url><loc>{u}</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>" for u in sorted(set(urls))])
    return Response(content=f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{xml_items}</urlset>', media_type="application/xml")