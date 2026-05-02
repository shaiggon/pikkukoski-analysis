from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.constants import BEACHES, find_files


def quality_int_to_label(value: int | float) -> str:
    return "good" if int(value) == 1 else "poor"


def quality_label_to_bad_probability(label: str) -> float:
    return 0.0 if label == "good" else 1.0


def load_curated_measurements(data_dir: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for beach in BEACHES:
        for file_path in find_files(data_dir, beach.historical_glob):
            frame = pd.read_csv(file_path)
            frame["date"] = pd.to_datetime(frame["date"]).dt.date
            for _, row in frame.iterrows():
                records.append(
                    {
                        "beach_id": beach.beach_id,
                        "measured_on": row["date"].isoformat(),
                        "quality_label": quality_int_to_label(row["quality"]),
                        "enterococci": float(row["enterococci"]),
                        "ecoli": float(row["ecoli"]),
                        "temperature_c": float(row["temperature"]) if not pd.isna(row["temperature"]) else None,
                        "blue_green_algae": int(row["blue_green_algae"]) if not pd.isna(row["blue_green_algae"]) else None,
                        "other_observations": int(row["other_observations"]) if not pd.isna(row["other_observations"]) else None,
                        "source": "curated_csv",
                        "source_document": file_path.name,
                    }
                )
    records.sort(key=lambda item: (str(item["measured_on"]), str(item["beach_id"])))
    return records

