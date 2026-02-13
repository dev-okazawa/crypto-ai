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
from ai.src.market_cap import get_supported, load_trained_symbols


# =====================
# App
# =====================

app = FastAPI(title="Crypto AI Prediction API")

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "ai" / "data" / "cache"
LOG_DIR = BASE_DIR / "logs"


# =====================
# Templates
# =====================

templates = Jinja2Templates(
    directory=str(BASE_DIR / "api" / "templates")
)


# =====================
# Static
# =====================

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
# HTML Pages
# =====================

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            **seo_context(
                title="Crypto AI Prediction",
                description="Crypto AI Prediction platform",
                keywords="crypto ai prediction",
                canonical="https://cryptoaipredict.com/",
            ),
        },
    )


@app.get("/visualize", response_class=HTMLResponse)
def visualize(request: Request):
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
def api_symbols(interval: str = "1h"):
    try:
        return get_supported(interval)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )


# =====================
# Market Overview API (interval対応)
# =====================

@app.get("/api/market-overview")
def api_market_overview(
    interval: str = Query("1h"),
    limit: int = Query(10, ge=1, le=200),
):
    try:
        allowed = {"1h", "1d", "1w"}

        if interval not in allowed:
            return JSONResponse(
                status_code=400,
                content={"error": "invalid interval"},
            )

        path = CACHE_DIR / f"market_overview_{interval}.json"

        if not path.exists():
            return JSONResponse(
                status_code=503,
                content={"error": f"{interval} cache not ready"},
            )

        data = json.loads(path.read_text())

        return {
            "items": data.get("items", [])[:limit],
            "meta": {
                **data.get("meta", {}),
                "interval": interval,
            },
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )


# =====================
# Stats API
# =====================

@app.get("/api/stats")
def api_stats():
    try:
        supported = get_supported("1h")
        supported_count = len(supported)
        supported_error = None
    except Exception as e:
        supported_count = 0
        supported_error = str(e)

    try:
        trained = load_trained_symbols()
        trained_count = len(trained)
    except Exception:
        trained_count = 0

    overview_path = CACHE_DIR / "market_overview_1h.json"
    overview_ready = 0
    overview_generated_at = None

    if overview_path.exists():
        try:
            data = json.loads(overview_path.read_text())
            overview_ready = len(data.get("items", []))
            overview_generated_at = data.get("meta", {}).get("generated_at")
        except Exception:
            pass

    cron_ok = (LOG_DIR / "cron_health.log").exists()

    return {
        "symbols": {
            "supported": supported_count,
            "trained_models": trained_count,
            "overview_ready": overview_ready,
        },
        "training": {
            "interval": "1h",
            "max_symbols": 200,
        },
        "system": {
            "cron_status": "ok" if cron_ok else "unknown",
            "checked_at": datetime.now(timezone.utc).isoformat(),
        },
        "debug": {
            "supported_error": supported_error,
            "overview_generated_at": overview_generated_at,
        },
    }


# =====================
# Sitemap
# =====================

@app.get("/sitemap.xml", response_class=Response)
def sitemap():

    base_url = "https://cryptoaipredict.com"

    urls = [
        "",
        "/visualize",
        "/about",
        "/privacy",
        "/terms",
        "/contact",
    ]

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for path in urls:
        xml += "  <url>\n"
        xml += f"    <loc>{base_url}{path}</loc>\n"
        xml += "  </url>\n"

    xml += "</urlset>"

    return Response(content=xml, media_type="application/xml")


# =====================
# Robots.txt
# =====================

@app.get("/robots.txt", response_class=Response)
def robots():

    content = """User-agent: *
Allow: /

Sitemap: https://cryptoaipredict.com/sitemap.xml
"""

    return Response(content=content, media_type="text/plain")



# =====================
# Accuracy API
# =====================

from ai.src.repository.db import get_connection


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
        return {
            "status": "ok",
            "accuracy": None,
            "mae": None,
            "total": 0
        }

    wins, total, mae = row

    if not total:
        return {
            "status": "ok",
            "accuracy": None,
            "mae": None,
            "total": 0
        }

    accuracy = round(wins / total * 100, 2)
    mae = round(mae, 2) if mae is not None else None

    return {
        "status": "ok",
        "accuracy": accuracy,
        "mae": mae,
        "total": total
    }
