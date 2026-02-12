import json
import traceback
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
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
                description=(
                    "Crypto AI Prediction is a web application that uses artificial "
                    "intelligence to predict cryptocurrency prices."
                ),
                keywords="crypto ai prediction, bitcoin ai, crypto forecast",
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
                keywords="crypto market ranking, ai crypto",
                canonical="https://cryptoaipredict.com/visualize",
            ),
        },
    )


# =====================
# 🆕 Legal / Info Pages
# =====================

@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            **seo_context(
                title="About | Crypto AI Prediction",
                description="About Crypto AI Prediction platform",
                keywords="about crypto ai prediction",
                canonical="https://cryptoaipredict.com/about",
            ),
        },
    )


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse(
        "privacy.html",
        {
            "request": request,
            **seo_context(
                title="Privacy Policy | Crypto AI Prediction",
                description="Privacy policy for Crypto AI Prediction",
                keywords="privacy policy crypto ai",
                canonical="https://cryptoaipredict.com/privacy",
            ),
        },
    )


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse(
        "terms.html",
        {
            "request": request,
            **seo_context(
                title="Terms of Service | Crypto AI Prediction",
                description="Terms of service for Crypto AI Prediction",
                keywords="terms crypto ai",
                canonical="https://cryptoaipredict.com/terms",
            ),
        },
    )


@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse(
        "contact.html",
        {
            "request": request,
            **seo_context(
                title="Contact | Crypto AI Prediction",
                description="Contact Crypto AI Prediction",
                keywords="contact crypto ai",
                canonical="https://cryptoaipredict.com/contact",
            ),
        },
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
# Market Overview API
# =====================

@app.get("/api/market-overview")
def api_market_overview(limit: int = 10):
    path = CACHE_DIR / "market_overview.json"

    if not path.exists():
        return JSONResponse(
            status_code=503,
            content={"error": "Market overview cache not ready"},
        )

    try:
        data = json.loads(path.read_text())
        return {
            "items": data.get("items", [])[:limit],
            "meta": data.get("meta", {}),
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

    overview_path = CACHE_DIR / "market_overview.json"
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
