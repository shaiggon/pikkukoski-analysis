from __future__ import annotations

import datetime as dt
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests

from app.constants import STATIONS, StationConfig, find_files

WEATHER_API_URL = "https://opendata.fmi.fi/wfs/fin"


def _historical_timestamp_to_utc(timestamp: pd.Timestamp, timezone: dt.tzinfo) -> pd.Timestamp:
    if timestamp.tzinfo is None:
        return timestamp.tz_localize(timezone).tz_convert(dt.timezone.utc)
    return timestamp.tz_convert(dt.timezone.utc)


def _normalize_fetched_timestamp(timestamp: str) -> str:
    parsed = pd.Timestamp(timestamp)
    if parsed.tzinfo is None:
        parsed = parsed.tz_localize(dt.timezone.utc)
    else:
        parsed = parsed.tz_convert(dt.timezone.utc)
    return parsed.isoformat()


def parse_fmi_response(xml_text: str, fetched_at: dt.datetime) -> list[dict[str, object]]:
    namespace = {
        "wml2": "http://www.opengis.net/waterml/2.0",
        "wfs": "http://www.opengis.net/wfs/2.0",
        "gml": "http://www.opengis.net/gml/3.2",
    }
    root = ET.fromstring(xml_text)
    records: list[dict[str, object]] = []
    fmi_place_to_station = {station.fmi_place: station.station_id for station in STATIONS}

    for member in root.findall("wfs:member", namespace):
        place_name = member.find(".//gml:name", namespace)
        if place_name is None or place_name.text is None:
            continue
        station_id = fmi_place_to_station.get(place_name.text.strip())
        if station_id is None:
            continue

        for point in member.findall(".//wml2:point", namespace):
            timestamp = point.find(".//wml2:time", namespace)
            value = point.find(".//wml2:value", namespace)
            if timestamp is None or timestamp.text is None or value is None or value.text is None:
                continue
            rain_mm = pd.to_numeric(value.text, errors="coerce")
            if pd.isna(rain_mm):
                continue
            records.append(
                {
                    "station_id": station_id,
                    "observed_at": _normalize_fetched_timestamp(timestamp.text),
                    "rain_mm": float(rain_mm),
                    "source": "fmi_api",
                    "ingested_at": fetched_at.isoformat(),
                }
            )
    records.sort(key=lambda item: (str(item["observed_at"]), str(item["station_id"])))
    return records


def fetch_weather_records(
    *,
    start_time: dt.datetime,
    end_time: dt.datetime,
    session: requests.Session | None = None,
) -> list[dict[str, object]]:
    client = session or requests.Session()
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "getFeature",
        "parameters": "PRA_PT1H_ACC",
        "timestep": "60",
        "storedquery_id": "fmi::observations::weather::hourly::timevaluepair",
        "starttime": start_time.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endtime": end_time.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "place": [station.fmi_place for station in STATIONS],
    }
    response = client.get(WEATHER_API_URL, params=params, timeout=30)
    response.raise_for_status()
    fetched_at = dt.datetime.now(dt.timezone.utc)
    return parse_fmi_response(response.text, fetched_at=fetched_at)


def read_historical_weather_file(
    file_path: Path,
    station: StationConfig,
    *,
    timezone: dt.tzinfo,
) -> list[dict[str, object]]:
    frame = pd.read_csv(file_path)
    frame["date"] = (
        frame["Vuosi"].astype(str)
        + "-"
        + frame["Kuukausi"].astype(str).str.zfill(2)
        + "-"
        + frame["Päivä"].astype(str).str.zfill(2)
        + " "
        + frame["Aika [Paikallinen aika]"]
    )
    frame["date"] = pd.to_datetime(frame["date"], format="%Y-%m-%d %H:%M")
    frame["Sademäärä [mm]"] = pd.to_numeric(frame["Sademäärä [mm]"], errors="coerce")
    frame = frame.dropna(subset=["date", "Sademäärä [mm]"])
    ingested_at = dt.datetime.now(dt.timezone.utc).isoformat()
    records: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        observed_at = _historical_timestamp_to_utc(pd.Timestamp(row["date"]), timezone)
        records.append(
            {
                "station_id": station.station_id,
                "observed_at": observed_at.isoformat(),
                "rain_mm": float(row["Sademäärä [mm]"]),
                "source": f"historical_csv:{file_path.name}",
                "ingested_at": ingested_at,
            }
        )
    return records


def load_historical_weather(data_dir: Path, *, timezone: dt.tzinfo) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for station in STATIONS:
        matching_files = find_files(data_dir, station.historical_glob)
        if station.station_id == "helsinki-vantaa":
            fixed_files = [file_path for file_path in matching_files if ".fixed." in file_path.name]
            if fixed_files:
                fixed_roots = {
                    file_path.name.replace(".fixed", "")
                    for file_path in fixed_files
                }
                matching_files = fixed_files + [
                    file_path
                    for file_path in matching_files
                    if file_path.name not in fixed_roots and ".fixed." not in file_path.name
                ]
        for file_path in matching_files:
            records.extend(read_historical_weather_file(file_path, station, timezone=timezone))
    records.sort(key=lambda item: (str(item["observed_at"]), str(item["station_id"])))
    return records
