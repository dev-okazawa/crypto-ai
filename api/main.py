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
# INDEX (SORT対応 + LastUpdated)
# =====================

@app.get("/", response_class=HTMLResponse)
def index(request: Request):

    interval = "1h"
    sort = request.query_params.get("sort")

    path = CACHE_DIR / f"market_overview_{interval}.json"
    coins = []
    generated_at = None  # 🔥 追加

    # 🔥 predictionと同じ並び取得
    supported = get_supported(interval)
    symbol_order = {c["symbol"]: i for i, c in enumerate(supported)}

    if path.exists():
        try:
            data = json.loads(path.read_text())

            # 🔥 ここで取得
            generated_at = data.get("meta", {}).get("generated_at")

            items = data.get("items", [])

            for item in items:

                data_block = item.get("data") or {}
                metrics = data_block.get("metrics") or {}
                prices = data_block.get("prices") or {}
                meta = item.get("meta") or {}

                past = prices.get("past") or []
                if not past:
                    continue

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

    # =====================
    # 🔥 ソートロジック
    # =====================

    if sort == "change_desc":
        coins.sort(key=lambda x: x["change_percent"], reverse=True)

    elif sort == "change_asc":
        coins.sort(key=lambda x: x["change_percent"])

    elif sort == "marketcap_asc":
        coins.sort(
            key=lambda x: symbol_order.get(x["symbol"], 9999),
            reverse=True
        )

    else:
        # 🔥 デフォルト（時価総額 大きい順）
        coins.sort(key=lambda x: symbol_order.get(x["symbol"], 9999))
        sort = "marketcap_desc"

    # =====================

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "coins": coins,
            "current_sort": sort,
            "last_updated": generated_at,  # 🔥 ここ重要
            **seo_context(
                title="Crypto AI Prediction",
                description="Crypto AI Prediction platform",
                keywords="crypto ai prediction",
                canonical="https://cryptoaipredict.com/",
            ),
        },
    )

# =====================
# Prediction Page
# =====================

@app.get("/prediction", response_class=HTMLResponse)
def prediction_page(
    request: Request,
    symbol: str = Query(None)
):

    return templates.TemplateResponse(
        "prediction.html",
        {
            "request": request,
            "initial_symbol": symbol or "",
            **seo_context(
                title="Prediction | Crypto AI",
                description="AI crypto price prediction",
                keywords="crypto prediction ai",
                canonical="https://cryptoaipredict.com/prediction",
            ),
        },
    )


# =====================
# Visualize Page
# =====================

@app.get("/visualize", response_class=HTMLResponse)
def visualize_page(request: Request):

    return templates.TemplateResponse(
        "visualize.html",
        {
            "request": request,
            **seo_context(
                title="Market Overview | Crypto AI",
                description="AI-powered crypto market overview",
                keywords="crypto market ranking",
                canonical="https://cryptoaipredict.com/visualize",
            ),
        },
    )


# =====================
# Static Pages
# =====================

@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse(
        "about.html",
        {"request": request, **seo_context(
            title="About",
            description="About Crypto AI",
            keywords="about",
            canonical="https://cryptoaipredict.com/about",
        )},
    )


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse(
        "privacy.html",
        {"request": request, **seo_context(
            title="Privacy Policy",
            description="Privacy Policy",
            keywords="privacy",
            canonical="https://cryptoaipredict.com/privacy",
        )},
    )


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse(
        "terms.html",
        {"request": request, **seo_context(
            title="Terms of Service",
            description="Terms",
            keywords="terms",
            canonical="https://cryptoaipredict.com/terms",
        )},
    )


@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse(
        "contact.html",
        {"request": request, **seo_context(
            title="Contact",
            description="Contact",
            keywords="contact",
            canonical="https://cryptoaipredict.com/contact",
        )},
    )


# =====================
# Prediction API
# =====================

@app.get("/predict")
def api_predict(
    symbol: str = Query(...),
    interval: str = Query("1h"),
    horizon: int = Query(1, ge=1, le=30),
):
    try:
        result = predict(symbol, interval, horizon)

        if result.get("status") != "ok":
            return result

        dto = build_prediction_dto(result)

        return {
            "meta": {
                "symbol": dto["symbol"],
                "interval": dto["meta"]["interval"],
                "timezone": "UTC",
                "last_update": int(
                    datetime.now(timezone.utc).timestamp() * 1000
                ),
            },
            "data": dto,
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
        )


# =====================
# Symbols API
# =====================

@app.get("/symbols")
def api_symbols(interval: str = Query("1h")):
    try:
        return get_supported(interval)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )


# =====================
# Market Overview API
# =====================

@app.get("/api/market-overview")
def api_market_overview(
    interval: str = Query("1h"),
    limit: int = Query(20, ge=1, le=200)
):

    path = CACHE_DIR / f"market_overview_{interval}.json"

    if not path.exists():
        return JSONResponse(
            status_code=503,
            content={"error": "Market overview cache not ready"},
        )

    try:
        data = json.loads(path.read_text())
        items = data.get("items", [])[:limit]

        return {
            "items": items,
            "meta": data.get("meta", {}),
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )


# =====================
# Accuracy API
# =====================

@app.get("/accuracy")
def get_accuracy(
    interval: str = Query(...),
    symbol: str = Query(...)
):

    conn = get_connection()
    cur = conn.cursor()

    horizon_map = {
        "1h": 3,
        "1d": 1,
        "1w": 1
    }

    horizon = horizon_map.get(interval, 3)

    cur.execute("""
        SELECT
          SUM(
            CASE
              WHEN (predicted_price - base_price) *
                   (actual_price - base_price) > 0
              THEN 1 ELSE 0
            END
          ) AS wins,
          COUNT(*) AS total,
          AVG(ABS(predicted_price - actual_price) / base_price) * 100 AS mae
        FROM predictions
        WHERE evaluated = 1
        AND timeframe = %s
        AND horizon = %s
    """, (interval, horizon))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return {"status": "ok", "accuracy": None, "mae": None, "total": 0}

    wins, total, mae = row

    if not total:
        return {"status": "ok", "accuracy": None, "mae": None, "total": 0}

    accuracy = round(wins / total * 100, 2)
    mae = round(mae, 2) if mae is not None else None

    return {
        "status": "ok",
        "accuracy": accuracy,
        "mae": mae,
        "total": total
    }


# =====================
# Dynamic Sitemap
# =====================

from fastapi.responses import Response
from datetime import datetime

@app.get("/sitemap.xml", include_in_schema=False)
def dynamic_sitemap():

    base_url = "https://cryptoaipredict.com"
    urls = []

    # =====================
    # ① FastAPIルートから自動取得
    # =====================
    for route in app.routes:
        if hasattr(route, "path"):
            path = route.path

            # 除外対象
            if (
                path.startswith("/api")
                or path.startswith("/static")
                or path.startswith("/health")
                or path.startswith("/docs")
                or path.startswith("/redoc")
                or path.startswith("/openapi")
                or path in ["/predict", "/symbols", "/accuracy"]
                or "{" in path  # パラメータ付き除外
                or path == "/sitemap.xml"
            ):
                continue

            urls.append(f"{base_url}{path}")

    # =====================
    # ② 銘柄ページを自動追加
    # =====================
    try:
        supported = get_supported("1h")
        for coin in supported:
            symbol = coin.get("symbol")
            if symbol:
                urls.append(f"{base_url}/prediction?symbol={symbol}")
    except Exception as e:
        print("SITEMAP SYMBOL LOAD ERROR:", e)

    # =====================
    # ③ XML生成
    # =====================
    now = datetime.utcnow().strftime("%Y-%m-%d")

    xml_items = ""
    for url in sorted(set(urls)):  # 重複除去＋ソート
        xml_items += f"""
    <url>
        <loc>{url}</loc>
        <lastmod>{now}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>"""

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{xml_items}
</urlset>
"""

    return Response(content=xml.strip(), media_type="application/xml")