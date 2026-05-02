from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from app.constants import PUBLIC_BEACH_ID
from app.settings import ensure_directories, get_settings
from app.storage import fetch_latest_prediction, fetch_prediction_history, fetch_recent_weather_for_station, init_db, open_db


settings = get_settings()
ensure_directories(settings)
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
app = FastAPI(title="Pikkukoski Water Quality")


@app.on_event("startup")
def startup() -> None:
    with open_db(settings.database_path) as connection:
        init_db(connection)


def _page_context() -> dict[str, object]:
    with open_db(settings.database_path) as connection:
        latest_prediction = fetch_latest_prediction(connection, PUBLIC_BEACH_ID)
        history = fetch_prediction_history(connection, PUBLIC_BEACH_ID, limit=10)
        recent_rain = fetch_recent_weather_for_station(connection, "kumpula", limit=24)

    feature_snapshot = {}
    if latest_prediction and latest_prediction.get("feature_snapshot_json"):
        feature_snapshot = json.loads(latest_prediction["feature_snapshot_json"])

    return {
        "prediction": latest_prediction,
        "history": history,
        "recent_rain": recent_rain,
        "feature_snapshot": feature_snapshot,
    }


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=_page_context(),
    )


@app.get("/api/status")
def api_status():
    context = _page_context()
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
