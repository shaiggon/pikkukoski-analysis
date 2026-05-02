from __future__ import annotations

import argparse
import datetime as dt

from app.constants import PUBLIC_BEACH_ID
from app.features import FEATURE_SPEC_VERSION
from app.modeling import generate_prediction, save_artifacts, train_models
from app.publish import write_public_artifacts
from app.settings import ensure_directories, get_settings
from app.storage import (
    fetch_measurements,
    fetch_weather_observations,
    init_db,
    insert_model_run,
    open_db,
    replace_measurements,
    upsert_daily_prediction,
    upsert_weather_observations,
)
from app.weather import fetch_weather_records, load_historical_weather
from app.measurements import load_curated_measurements


def init_database() -> None:
    settings = get_settings()
    ensure_directories(settings)
    with open_db(settings.database_path) as connection:
        init_db(connection)
    print(f"Initialised SQLite database at {settings.database_path}")


def import_measurements() -> None:
    settings = get_settings()
    ensure_directories(settings)
    records = load_curated_measurements(settings.data_dir)
    with open_db(settings.database_path) as connection:
        init_db(connection)
        count = replace_measurements(connection, records)
    print(f"Imported {count} curated measurement rows")


def import_historical_weather() -> None:
    settings = get_settings()
    ensure_directories(settings)
    records = load_historical_weather(settings.data_dir, timezone=settings.timezone)
    with open_db(settings.database_path) as connection:
        init_db(connection)
        count = upsert_weather_observations(connection, records)
    print(f"Imported {count} historical weather rows")


def ingest_weather(hours: int) -> None:
    settings = get_settings()
    ensure_directories(settings)
    end_time = dt.datetime.now(dt.timezone.utc)
    start_time = end_time - dt.timedelta(hours=hours)
    records = fetch_weather_records(start_time=start_time, end_time=end_time)
    with open_db(settings.database_path) as connection:
        init_db(connection)
        count = upsert_weather_observations(connection, records)
    print(f"Fetched and upserted {count} weather observations")


def train() -> None:
    settings = get_settings()
    ensure_directories(settings)
    with open_db(settings.database_path) as connection:
        init_db(connection)
        weather_records = fetch_weather_observations(connection)
        measurement_records = fetch_measurements(connection, beach_id=PUBLIC_BEACH_ID)

    artifacts = train_models(weather_records, measurement_records, timezone=settings.timezone)
    save_artifacts(artifacts, settings.models_dir)

    with open_db(settings.database_path) as connection:
        model_run_id = insert_model_run(
            connection,
            trained_at=dt.datetime.now(dt.timezone.utc).isoformat(),
            feature_spec_version=FEATURE_SPEC_VERSION,
            classification_model_type=type(artifacts.classification_model).__name__,
            regression_model_type=type(artifacts.regression_model).__name__,
            metrics=artifacts.metrics,
        )
    print(f"Trained models and recorded model_run {model_run_id}")


def predict() -> None:
    settings = get_settings()
    ensure_directories(settings)
    with open_db(settings.database_path) as connection:
        init_db(connection)
        weather_records = fetch_weather_observations(connection)
        latest_model_run = connection.execute("SELECT id FROM model_run ORDER BY id DESC LIMIT 1").fetchone()
        if latest_model_run is None:
            raise RuntimeError("No model_run found. Train models before generating predictions.")

        prediction = generate_prediction(weather_records, timezone=settings.timezone, models_dir=settings.models_dir)
        prediction_record = {
            "beach_id": PUBLIC_BEACH_ID,
            "predicted_for": prediction["predicted_for"],
            "quality_probability_bad": prediction["quality_probability_bad"],
            "quality_label_predicted": prediction["quality_label_predicted"],
            "enterococci_predicted": prediction["enterococci_predicted"],
            "ecoli_predicted": prediction["ecoli_predicted"],
            "feature_snapshot": prediction["feature_snapshot"],
            "model_run_id": int(latest_model_run["id"]),
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        upsert_daily_prediction(connection, prediction_record)
    print(f"Generated prediction for {PUBLIC_BEACH_ID} on {prediction['predicted_for']}")


def publish() -> None:
    settings = get_settings()
    ensure_directories(settings)
    with open_db(settings.database_path) as connection:
        init_db(connection)
        write_public_artifacts(connection, settings.output_dir)
    print(f"Wrote public artifacts to {settings.output_dir}")


def refresh_all() -> None:
    init_database()
    import_measurements()
    import_historical_weather()
    train()
    predict()
    publish()


def main() -> None:
    parser = argparse.ArgumentParser(description="Pikkukoski app CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db")
    subparsers.add_parser("import-measurements")
    subparsers.add_parser("import-historical-weather")

    ingest_parser = subparsers.add_parser("ingest-weather")
    ingest_parser.add_argument("--hours", type=int, default=126)

    subparsers.add_parser("train-models")
    subparsers.add_parser("generate-predictions")
    subparsers.add_parser("publish-site-data")
    subparsers.add_parser("refresh-all")

    args = parser.parse_args()
    if args.command == "init-db":
        init_database()
    elif args.command == "import-measurements":
        import_measurements()
    elif args.command == "import-historical-weather":
        import_historical_weather()
    elif args.command == "ingest-weather":
        ingest_weather(args.hours)
    elif args.command == "train-models":
        train()
    elif args.command == "generate-predictions":
        predict()
    elif args.command == "publish-site-data":
        publish()
    elif args.command == "refresh-all":
        refresh_all()
    else:
        raise ValueError(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
