from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import GroupKFold, cross_validate

from app.constants import PUBLIC_BEACH_ID
from app.features import FEATURE_SPEC_VERSION, build_current_feature_row, build_training_dataset, prediction_band_from_probability


@dataclass
class TrainedArtifacts:
    classification_model: LogisticRegression
    regression_model: Ridge
    feature_columns: list[str]
    metrics: dict[str, object]


def _cv_splits(groups: pd.Series) -> GroupKFold | None:
    unique_groups = groups.nunique()
    if unique_groups < 2:
        return None
    return GroupKFold(n_splits=min(unique_groups, 4))


def _cross_validation_metrics(
    x_features: pd.DataFrame,
    y_quality: pd.Series,
    y_regression: pd.DataFrame,
    groups: pd.Series,
) -> dict[str, object]:
    split_strategy = _cv_splits(groups)
    if split_strategy is None:
        return {"note": "Not enough distinct years for grouped cross-validation"}

    classification_scores = cross_validate(
        LogisticRegression(max_iter=1000),
        x_features,
        y_quality,
        groups=groups,
        cv=split_strategy,
        scoring=("accuracy", "f1"),
    )
    regression_scores = cross_validate(
        Ridge(alpha=1.0),
        x_features,
        y_regression,
        groups=groups,
        cv=split_strategy,
        scoring=("neg_mean_absolute_error", "r2"),
    )
    return {
        "classification_accuracy_mean": float(np.mean(classification_scores["test_accuracy"])),
        "classification_f1_mean": float(np.mean(classification_scores["test_f1"])),
        "regression_neg_mae_mean": float(np.mean(regression_scores["test_neg_mean_absolute_error"])),
        "regression_r2_mean": float(np.mean(regression_scores["test_r2"])),
    }


def train_models(
    weather_records: list[dict[str, object]],
    measurement_records: list[dict[str, object]],
    *,
    timezone,
) -> TrainedArtifacts:
    x_frame, y_frame = build_training_dataset(
        weather_records,
        measurement_records,
        beach_id=PUBLIC_BEACH_ID,
        timezone=timezone,
    )
    if x_frame.empty or y_frame.empty:
        raise ValueError("Training dataset is empty")

    feature_columns = [column for column in x_frame.columns if column != "measured_on"]
    x_features = x_frame[feature_columns]
    y_quality = y_frame["quality_bad"]
    y_regression = y_frame[["enterococci", "ecoli"]]
    groups = pd.to_datetime(x_frame["measured_on"]).dt.year

    metrics = _cross_validation_metrics(x_features, y_quality, y_regression, groups)

    classification_model = LogisticRegression(max_iter=1000)
    classification_model.fit(x_features, y_quality)

    regression_model = Ridge(alpha=1.0)
    regression_model.fit(x_features, y_regression)

    return TrainedArtifacts(
        classification_model=classification_model,
        regression_model=regression_model,
        feature_columns=feature_columns,
        metrics=metrics,
    )


def save_artifacts(artifacts: TrainedArtifacts, models_dir: Path) -> None:
    models_dir.mkdir(parents=True, exist_ok=True)
    with (models_dir / "classification.pkl").open("wb") as handle:
        pickle.dump(artifacts.classification_model, handle)
    with (models_dir / "regression.pkl").open("wb") as handle:
        pickle.dump(artifacts.regression_model, handle)
    metadata = {
        "feature_columns": artifacts.feature_columns,
        "feature_spec_version": FEATURE_SPEC_VERSION,
        "metrics": artifacts.metrics,
        "classification_model_type": type(artifacts.classification_model).__name__,
        "regression_model_type": type(artifacts.regression_model).__name__,
    }
    (models_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True))


def load_artifacts(models_dir: Path) -> tuple[LogisticRegression, Ridge, dict[str, object]]:
    with (models_dir / "classification.pkl").open("rb") as handle:
        classification_model = pickle.load(handle)
    with (models_dir / "regression.pkl").open("rb") as handle:
        regression_model = pickle.load(handle)
    metadata = json.loads((models_dir / "metadata.json").read_text())
    return classification_model, regression_model, metadata


def generate_prediction(
    weather_records: list[dict[str, object]],
    *,
    timezone,
    models_dir: Path,
) -> dict[str, object]:
    classification_model, regression_model, metadata = load_artifacts(models_dir)
    latest_time, current_features = build_current_feature_row(weather_records, timezone=timezone)
    feature_columns = metadata["feature_columns"]
    feature_vector = current_features[feature_columns]
    probability_bad = float(classification_model.predict_proba(feature_vector)[0][1])
    enterococci_predicted, ecoli_predicted = regression_model.predict(feature_vector)[0]
    return {
        "feature_spec_version": metadata["feature_spec_version"],
        "feature_snapshot": {key: float(value) for key, value in feature_vector.iloc[0].to_dict().items()},
        "predicted_for": latest_time.date().isoformat(),
        "latest_feature_time_local": latest_time.isoformat(),
        "quality_probability_bad": probability_bad,
        "quality_label_predicted": prediction_band_from_probability(probability_bad),
        "enterococci_predicted": float(enterococci_predicted),
        "ecoli_predicted": float(ecoli_predicted),
    }

