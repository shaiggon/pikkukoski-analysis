from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StationConfig:
    station_id: str
    display_name: str
    fmi_place: str
    fmi_name_aliases: tuple[str, ...]
    historical_glob: str
    source_name: str


@dataclass(frozen=True)
class BeachConfig:
    beach_id: str
    display_name: str
    historical_glob: str


STATIONS: tuple[StationConfig, ...] = (
    StationConfig(
        station_id="kumpula",
        display_name="Kumpula",
        fmi_place="kumpula",
        fmi_name_aliases=("kumpula", "helsinki kumpula"),
        historical_glob="Helsinki Kumpula*.csv",
        source_name="fmi",
    ),
    StationConfig(
        station_id="helsinki-vantaa",
        display_name="Helsinki-Vantaa",
        fmi_place="helsinki-vantaan_lentoasema",
        fmi_name_aliases=("helsinki-vantaan_lentoasema", "vantaa helsinki-vantaan lentoasema"),
        historical_glob="Vantaa Helsinki-*.csv",
        source_name="fmi",
    ),
)

BEACHES: tuple[BeachConfig, ...] = (
    BeachConfig(
        beach_id="pikkukoski",
        display_name="Pikkukoski",
        historical_glob="pikkukoski_*.csv",
    ),
    BeachConfig(
        beach_id="pakila",
        display_name="Pakila",
        historical_glob="pakila_*.csv",
    ),
    BeachConfig(
        beach_id="tapaninvainio",
        display_name="Tapaninvainio",
        historical_glob="tapaninvainio_*.csv",
    ),
)

PUBLIC_BEACH_ID = "pikkukoski"
FEATURE_RESAMPLE_RATE = "6h"
FEATURE_LAG_COUNT = 8
FEATURE_ROLLING_WINDOW = 8


def station_by_id(station_id: str) -> StationConfig:
    for station in STATIONS:
        if station.station_id == station_id:
            return station
    raise KeyError(f"Unknown station_id: {station_id}")


def beach_by_id(beach_id: str) -> BeachConfig:
    for beach in BEACHES:
        if beach.beach_id == beach_id:
            return beach
    raise KeyError(f"Unknown beach_id: {beach_id}")


def find_files(data_dir: Path, pattern: str) -> list[Path]:
    return sorted(data_dir.glob(pattern))
