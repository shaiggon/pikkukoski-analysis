from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator


def connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def open_db(db_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(db_path)
    try:
        yield connection
    finally:
        connection.close()


def init_db(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS weather_observation (
            station_id TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            rain_mm REAL NOT NULL,
            source TEXT NOT NULL,
            ingested_at TEXT NOT NULL,
            PRIMARY KEY (station_id, observed_at)
        );

        CREATE TABLE IF NOT EXISTS water_quality_measurement (
            beach_id TEXT NOT NULL,
            measured_on TEXT NOT NULL,
            quality_label TEXT NOT NULL,
            enterococci REAL NOT NULL,
            ecoli REAL NOT NULL,
            temperature_c REAL,
            blue_green_algae INTEGER,
            other_observations INTEGER,
            source TEXT NOT NULL,
            source_document TEXT,
            PRIMARY KEY (beach_id, measured_on)
        );

        CREATE TABLE IF NOT EXISTS model_run (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trained_at TEXT NOT NULL,
            feature_spec_version TEXT NOT NULL,
            classification_model_type TEXT NOT NULL,
            regression_model_type TEXT NOT NULL,
            metrics_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS daily_prediction (
            beach_id TEXT NOT NULL,
            predicted_for TEXT NOT NULL,
            quality_probability_bad REAL NOT NULL,
            quality_label_predicted TEXT NOT NULL,
            enterococci_predicted REAL NOT NULL,
            ecoli_predicted REAL NOT NULL,
            feature_snapshot_json TEXT NOT NULL,
            model_run_id INTEGER NOT NULL,
            generated_at TEXT NOT NULL,
            PRIMARY KEY (beach_id, predicted_for),
            FOREIGN KEY (model_run_id) REFERENCES model_run(id)
        );
        """
    )
    connection.commit()


def upsert_weather_observations(connection: sqlite3.Connection, records: Iterable[dict[str, Any]]) -> int:
    rows = [
        (
            record["station_id"],
            record["observed_at"],
            float(record["rain_mm"]),
            record["source"],
            record["ingested_at"],
        )
        for record in records
    ]
    if not rows:
        return 0
    connection.executemany(
        """
        INSERT INTO weather_observation (station_id, observed_at, rain_mm, source, ingested_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(station_id, observed_at) DO UPDATE SET
            rain_mm = excluded.rain_mm,
            source = excluded.source,
            ingested_at = excluded.ingested_at
        """,
        rows,
    )
    connection.commit()
    return len(rows)


def replace_measurements(connection: sqlite3.Connection, records: Iterable[dict[str, Any]]) -> int:
    rows = [
        (
            record["beach_id"],
            record["measured_on"],
            record["quality_label"],
            float(record["enterococci"]),
            float(record["ecoli"]),
            record.get("temperature_c"),
            record.get("blue_green_algae"),
            record.get("other_observations"),
            record["source"],
            record.get("source_document"),
        )
        for record in records
    ]
    if not rows:
        return 0
    connection.executemany(
        """
        INSERT INTO water_quality_measurement (
            beach_id, measured_on, quality_label, enterococci, ecoli, temperature_c,
            blue_green_algae, other_observations, source, source_document
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(beach_id, measured_on) DO UPDATE SET
            quality_label = excluded.quality_label,
            enterococci = excluded.enterococci,
            ecoli = excluded.ecoli,
            temperature_c = excluded.temperature_c,
            blue_green_algae = excluded.blue_green_algae,
            other_observations = excluded.other_observations,
            source = excluded.source,
            source_document = excluded.source_document
        """,
        rows,
    )
    connection.commit()
    return len(rows)


def insert_model_run(
    connection: sqlite3.Connection,
    *,
    trained_at: str,
    feature_spec_version: str,
    classification_model_type: str,
    regression_model_type: str,
    metrics: dict[str, Any],
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO model_run (
            trained_at, feature_spec_version, classification_model_type,
            regression_model_type, metrics_json
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            trained_at,
            feature_spec_version,
            classification_model_type,
            regression_model_type,
            json.dumps(metrics, sort_keys=True),
        ),
    )
    connection.commit()
    return int(cursor.lastrowid)


def upsert_daily_prediction(connection: sqlite3.Connection, record: dict[str, Any]) -> None:
    connection.execute(
        """
        INSERT INTO daily_prediction (
            beach_id, predicted_for, quality_probability_bad, quality_label_predicted,
            enterococci_predicted, ecoli_predicted, feature_snapshot_json, model_run_id, generated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(beach_id, predicted_for) DO UPDATE SET
            quality_probability_bad = excluded.quality_probability_bad,
            quality_label_predicted = excluded.quality_label_predicted,
            enterococci_predicted = excluded.enterococci_predicted,
            ecoli_predicted = excluded.ecoli_predicted,
            feature_snapshot_json = excluded.feature_snapshot_json,
            model_run_id = excluded.model_run_id,
            generated_at = excluded.generated_at
        """,
        (
            record["beach_id"],
            record["predicted_for"],
            float(record["quality_probability_bad"]),
            record["quality_label_predicted"],
            float(record["enterococci_predicted"]),
            float(record["ecoli_predicted"]),
            json.dumps(record["feature_snapshot"], sort_keys=True),
            int(record["model_run_id"]),
            record["generated_at"],
        ),
    )
    connection.commit()


def fetch_weather_observations(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT station_id, observed_at, rain_mm, source, ingested_at
        FROM weather_observation
        ORDER BY observed_at ASC, station_id ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def fetch_measurements(connection: sqlite3.Connection, beach_id: str | None = None) -> list[dict[str, Any]]:
    if beach_id is None:
        rows = connection.execute(
            """
            SELECT *
            FROM water_quality_measurement
            ORDER BY measured_on ASC, beach_id ASC
            """
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT *
            FROM water_quality_measurement
            WHERE beach_id = ?
            ORDER BY measured_on ASC
            """,
            (beach_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def fetch_latest_model_run(connection: sqlite3.Connection) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT *
        FROM model_run
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    return dict(row) if row is not None else None


def fetch_latest_prediction(connection: sqlite3.Connection, beach_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT dp.*, m.measured_on, m.enterococci AS measured_enterococci, m.ecoli AS measured_ecoli,
               m.quality_label AS measured_quality_label
        FROM daily_prediction dp
        LEFT JOIN water_quality_measurement m
            ON m.beach_id = dp.beach_id
           AND m.measured_on = (
                SELECT MAX(measured_on)
                FROM water_quality_measurement
                WHERE beach_id = dp.beach_id
           )
        WHERE dp.beach_id = ?
        ORDER BY dp.predicted_for DESC
        LIMIT 1
        """,
        (beach_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def fetch_prediction_history(connection: sqlite3.Connection, beach_id: str, limit: int = 30) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT *
        FROM daily_prediction
        WHERE beach_id = ?
        ORDER BY predicted_for DESC
        LIMIT ?
        """,
        (beach_id, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def fetch_recent_weather_for_station(
    connection: sqlite3.Connection,
    station_id: str,
    limit: int = 56,
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT station_id, observed_at, rain_mm
        FROM weather_observation
        WHERE station_id = ?
        ORDER BY observed_at DESC
        LIMIT ?
        """,
        (station_id, limit),
    ).fetchall()
    return [dict(row) for row in reversed(rows)]

