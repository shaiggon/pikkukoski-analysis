from __future__ import annotations

import json
from pathlib import Path

from app.constants import PUBLIC_BEACH_ID
from app.storage import fetch_latest_prediction, fetch_prediction_history, fetch_recent_weather_for_station


def write_public_artifacts(connection, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_prediction = fetch_latest_prediction(connection, PUBLIC_BEACH_ID)
    history = fetch_prediction_history(connection, PUBLIC_BEACH_ID, limit=120)
    rain_history = fetch_recent_weather_for_station(connection, "kumpula", limit=56)

    (output_dir / "current_status.json").write_text(
        json.dumps(latest_prediction or {}, indent=2, sort_keys=True)
    )
    (output_dir / "history.json").write_text(
        json.dumps(
            {
                "predictions": history,
                "recent_rain_kumpula": rain_history,
            },
            indent=2,
            sort_keys=True,
        )
    )
