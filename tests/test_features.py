import datetime as dt
from zoneinfo import ZoneInfo

from app.features import build_training_dataset, prediction_band_from_probability, threshold_label_from_bacteria


def _weather_record(station_id: str, observed_at: str, rain_mm: float) -> dict[str, object]:
    return {
        "station_id": station_id,
        "observed_at": observed_at,
        "rain_mm": rain_mm,
        "source": "test",
        "ingested_at": "2026-05-01T00:00:00+00:00",
    }


def test_threshold_label_from_bacteria() -> None:
    assert threshold_label_from_bacteria(100, 200) == "good"
    assert threshold_label_from_bacteria(401, 200) == "poor"
    assert threshold_label_from_bacteria(100, 1001) == "poor"


def test_prediction_band_from_probability() -> None:
    assert prediction_band_from_probability(0.2) == "good"
    assert prediction_band_from_probability(0.5) == "elevated-risk"
    assert prediction_band_from_probability(0.8) == "poor"


def test_build_training_dataset_merges_weather_and_measurements() -> None:
    timezone = ZoneInfo("Europe/Helsinki")
    weather_records = [
        _weather_record("kumpula", "2024-06-03T15:00:00+00:00", 1.0),
        _weather_record("kumpula", "2024-06-03T21:00:00+00:00", 0.5),
        _weather_record("kumpula", "2024-06-04T03:00:00+00:00", 0.0),
        _weather_record("kumpula", "2024-06-04T09:00:00+00:00", 2.0),
        _weather_record("kumpula", "2024-06-04T15:00:00+00:00", 0.0),
        _weather_record("kumpula", "2024-06-04T21:00:00+00:00", 0.1),
        _weather_record("kumpula", "2024-06-05T03:00:00+00:00", 0.0),
        _weather_record("kumpula", "2024-06-05T09:00:00+00:00", 3.0),
        _weather_record("helsinki-vantaa", "2024-06-03T15:00:00+00:00", 0.7),
        _weather_record("helsinki-vantaa", "2024-06-03T21:00:00+00:00", 0.2),
        _weather_record("helsinki-vantaa", "2024-06-04T03:00:00+00:00", 0.0),
        _weather_record("helsinki-vantaa", "2024-06-04T09:00:00+00:00", 1.0),
        _weather_record("helsinki-vantaa", "2024-06-04T15:00:00+00:00", 0.0),
        _weather_record("helsinki-vantaa", "2024-06-04T21:00:00+00:00", 0.0),
        _weather_record("helsinki-vantaa", "2024-06-05T03:00:00+00:00", 0.3),
        _weather_record("helsinki-vantaa", "2024-06-05T09:00:00+00:00", 1.8),
    ]
    measurement_records = [
        {
            "beach_id": "pikkukoski",
            "measured_on": "2024-06-05",
            "quality_label": "good",
            "enterococci": 30.0,
            "ecoli": 50.0,
        }
    ]

    x_frame, y_frame = build_training_dataset(
        weather_records,
        measurement_records,
        beach_id="pikkukoski",
        timezone=timezone,
    )

    assert len(x_frame) == 1
    assert len(y_frame) == 1
    assert "kumpula_rain_now" in x_frame.columns
    assert "helsinki-vantaa_rain_lag1" in x_frame.columns

