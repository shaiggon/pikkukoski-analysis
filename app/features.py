from __future__ import annotations

import datetime as dt

import pandas as pd

from app.constants import FEATURE_LAG_COUNT, FEATURE_RESAMPLE_RATE, FEATURE_ROLLING_WINDOW


FEATURE_SPEC_VERSION = (
    f"rain-v1-resample-{FEATURE_RESAMPLE_RATE}-lag-{FEATURE_LAG_COUNT}-rolling-{FEATURE_ROLLING_WINDOW}"
)


def threshold_label_from_bacteria(enterococci: float, ecoli: float) -> str:
    return "poor" if enterococci > 400 or ecoli > 1000 else "good"


def prediction_band_from_probability(probability_bad: float) -> str:
    if probability_bad >= 0.6:
        return "poor"
    if probability_bad >= 0.35:
        return "elevated-risk"
    return "good"


def weather_records_to_frame(records: list[dict[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame.from_records(records)
    if frame.empty:
        return pd.DataFrame(columns=["station_id", "observed_at", "rain_mm"])
    frame["observed_at"] = pd.to_datetime(frame["observed_at"], utc=True)
    frame["rain_mm"] = pd.to_numeric(frame["rain_mm"], errors="coerce").fillna(0.0)
    return frame.sort_values(["observed_at", "station_id"]).reset_index(drop=True)


def measurement_records_to_frame(records: list[dict[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame.from_records(records)
    if frame.empty:
        return pd.DataFrame(
            columns=["beach_id", "measured_on", "quality_label", "enterococci", "ecoli"]
        )
    frame["measured_on"] = pd.to_datetime(frame["measured_on"]).dt.date
    frame["quality_bad"] = (frame["quality_label"] == "poor").astype(int)
    return frame.sort_values(["measured_on", "beach_id"]).reset_index(drop=True)


def build_weather_feature_frame(
    weather_frame: pd.DataFrame,
    *,
    timezone: dt.tzinfo,
    resample_rate: str = FEATURE_RESAMPLE_RATE,
    lag_count: int = FEATURE_LAG_COUNT,
    rolling_window: int = FEATURE_ROLLING_WINDOW,
) -> pd.DataFrame:
    if weather_frame.empty:
        return pd.DataFrame()

    weather_frame = weather_frame.copy()
    weather_frame["observed_local"] = weather_frame["observed_at"].dt.tz_convert(timezone)
    weather_frame = weather_frame.set_index("observed_local")

    station_frames: list[pd.DataFrame] = []
    for station_id, station_data in weather_frame.groupby("station_id"):
        station_series = station_data[["rain_mm"]].resample(resample_rate).sum().fillna(0.0)
        station_features = pd.DataFrame(index=station_series.index)
        station_features[f"{station_id}_rain_now"] = station_series["rain_mm"]
        for lag in range(1, lag_count + 1):
            station_features[f"{station_id}_rain_lag{lag}"] = station_series["rain_mm"].shift(lag)
        station_features[f"{station_id}_rain_rolling_sum{rolling_window}"] = (
            station_series["rain_mm"].rolling(rolling_window).sum()
        )
        station_features[f"{station_id}_rain_rolling_mean{rolling_window}"] = (
            station_series["rain_mm"].rolling(rolling_window).mean()
        )
        station_frames.append(station_features)

    merged = pd.concat(station_frames, axis=1, join="inner").dropna()
    merged.index.name = "feature_time_local"
    return merged.sort_index()


def build_training_dataset(
    weather_records: list[dict[str, object]],
    measurement_records: list[dict[str, object]],
    *,
    beach_id: str,
    timezone: dt.tzinfo,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    weather_frame = weather_records_to_frame(weather_records)
    measurement_frame = measurement_records_to_frame(measurement_records)
    measurement_frame = measurement_frame[measurement_frame["beach_id"] == beach_id].copy()
    if weather_frame.empty or measurement_frame.empty:
        return pd.DataFrame(), pd.DataFrame()

    feature_frame = build_weather_feature_frame(weather_frame, timezone=timezone)
    if feature_frame.empty:
        return pd.DataFrame(), pd.DataFrame()

    feature_frame = feature_frame.copy()
    feature_frame["measured_on"] = feature_frame.index.date
    feature_frame = feature_frame.drop_duplicates(subset=["measured_on"], keep="last")
    merged = measurement_frame.merge(feature_frame, on="measured_on", how="inner")
    if merged.empty:
        return pd.DataFrame(), pd.DataFrame()

    feature_columns = [column for column in merged.columns if "_rain_" in column]
    target_columns = ["measured_on", "quality_bad", "enterococci", "ecoli"]
    x_frame = merged[["measured_on", *feature_columns]].copy()
    y_frame = merged[target_columns].copy()
    return x_frame, y_frame


def build_current_feature_row(
    weather_records: list[dict[str, object]],
    *,
    timezone: dt.tzinfo,
) -> tuple[pd.Timestamp, pd.DataFrame]:
    weather_frame = weather_records_to_frame(weather_records)
    feature_frame = build_weather_feature_frame(weather_frame, timezone=timezone)
    if feature_frame.empty:
        raise ValueError("Not enough weather data to build current features")
    latest_index = feature_frame.index.max()
    current = feature_frame.loc[[latest_index]].copy()
    return latest_index, current

