from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.constants import PUBLIC_BEACH_ID
from app.features import POOR_PROBABILITY_THRESHOLD, WARNING_PROBABILITY_THRESHOLD
from app.presentation import (
    build_history_chart,
    build_probability_thresholds,
    build_rain_chart,
    build_threshold_gauge,
    copy_for_language,
    format_date,
    format_timestamp,
    language_options,
    localize_status,
    resolve_language,
)
from app.settings import ensure_directories, get_settings
from app.storage import fetch_latest_prediction, fetch_prediction_history, fetch_recent_weather_for_station, init_db, open_db


APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"
PUBLIC_WEATHER_STATION_ID = "kumpula"
PAGE_HISTORY_LIMIT = 10
PAGE_RAIN_LIMIT = 24

settings = get_settings()
ensure_directories(settings)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app = FastAPI(title="Pikkukoski Water Quality")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
def startup() -> None:
    with open_db(settings.database_path) as connection:
        init_db(connection)


def _feature_snapshot(latest_prediction: dict[str, Any] | None) -> dict[str, Any]:
    if latest_prediction and latest_prediction.get("feature_snapshot_json"):
        return json.loads(latest_prediction["feature_snapshot_json"])
    return {}


def _localized_prediction(
    latest_prediction: dict[str, Any] | None,
    lang: str,
    copy: dict[str, str],
) -> dict[str, Any] | None:
    if latest_prediction is None:
        return None

    localized_prediction = dict(latest_prediction)
    localized_prediction["predicted_at_display"] = format_timestamp(latest_prediction.get("predicted_at"))
    localized_prediction["measured_on_display"] = format_date(latest_prediction.get("measured_on"))
    localized_prediction["quality_label_display"] = localize_status(lang, latest_prediction.get("quality_label_predicted"))
    localized_prediction["measured_quality_label_display"] = localize_status(
        lang, latest_prediction.get("measured_quality_label")
    )
    localized_prediction["predicted_at_sentence"] = copy["predicted_at"].replace(
        "{timestamp}", localized_prediction["predicted_at_display"] or ""
    )
    localized_prediction["bad_water_probability_sentence"] = copy["bad_water_probability"].replace(
        "{value}", f'{latest_prediction["quality_probability_bad"] * 100:.0f}'
    )
    return localized_prediction


def _threshold_gauges(latest_prediction: dict[str, Any] | None) -> dict[str, dict[str, Any]] | None:
    if latest_prediction is None:
        return None
    return {
        "enterococci": build_threshold_gauge(
            "enterococci",
            latest_prediction.get("enterococci_predicted"),
            latest_prediction.get("measured_enterococci"),
        ),
        "ecoli": build_threshold_gauge(
            "ecoli",
            latest_prediction.get("ecoli_predicted"),
            latest_prediction.get("measured_ecoli"),
        ),
    }


def _page_context(lang: str | None) -> dict[str, object]:
    resolved_lang = resolve_language(lang)
    copy = copy_for_language(resolved_lang)
    with open_db(settings.database_path) as connection:
        latest_prediction = fetch_latest_prediction(connection, PUBLIC_BEACH_ID)
        history = fetch_prediction_history(connection, PUBLIC_BEACH_ID, limit=PAGE_HISTORY_LIMIT)
        recent_rain = fetch_recent_weather_for_station(connection, PUBLIC_WEATHER_STATION_ID, limit=PAGE_RAIN_LIMIT)

    return {
        "prediction": latest_prediction,
        "localized_prediction": _localized_prediction(latest_prediction, resolved_lang, copy),
        "history": history,
        "recent_rain": recent_rain,
        "feature_snapshot": _feature_snapshot(latest_prediction),
        "lang": resolved_lang,
        "copy": copy,
        "language_options": language_options(resolved_lang),
        "probability_thresholds": build_probability_thresholds(
            WARNING_PROBABILITY_THRESHOLD,
            POOR_PROBABILITY_THRESHOLD,
        ),
        "rain_chart": build_rain_chart(recent_rain),
        "history_chart": build_history_chart(history, resolved_lang),
        "threshold_gauges": _threshold_gauges(latest_prediction),
    }


@app.get("/")
def index(request: Request, lang: str | None = None):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=_page_context(lang),
    )


@app.get("/api/status")
def api_status():
    context = _page_context(None)
    return JSONResponse(
        {
            "prediction": context["prediction"],
            "recent_rain": context["recent_rain"],
            "feature_snapshot": context["feature_snapshot"],
        }
    )


@app.get("/api/history")
def api_history(days: int = 30):
    with open_db(settings.database_path) as connection:
        history = fetch_prediction_history(connection, PUBLIC_BEACH_ID, limit=max(days * 4, 24))
        recent_rain = fetch_recent_weather_for_station(connection, "kumpula", limit=max(days * 4, 24))
    return JSONResponse({"predictions": history, "recent_rain": recent_rain})


@app.get("/health")
def health():
    with open_db(settings.database_path) as connection:
        connection.execute("SELECT 1").fetchone()
    return {"status": "ok"}
