from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, precision_score, r2_score, recall_score
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut, cross_validate, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.constants import PUBLIC_BEACH_ID
from app.features import (
    FEATURE_SPEC_VERSION,
    WARNING_PROBABILITY_THRESHOLD,
    build_prediction_feature_rows,
    build_training_dataset,
    prediction_band_from_probability,
)


@dataclass
class TrainedArtifacts:
    classification_model: LogisticRegression
    regression_model: object
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
        make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
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


def evaluate_models(
    weather_records: list[dict[str, object]],
    measurement_records: list[dict[str, object]],
    *,
    timezone,
) -> dict[str, object]:
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
    y_regression_log = np.log1p(y_regression)
    groups = pd.to_datetime(x_frame["measured_on"]).dt.year

    cv = LeaveOneGroupOut()
    classification_model = LogisticRegression(max_iter=1000)
    regression_model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))

    cls_oof = cross_val_predict(classification_model, x_features, y_quality, groups=groups, cv=cv, method="predict")
    cls_oof_proba = cross_val_predict(
        classification_model, x_features, y_quality, groups=groups, cv=cv, method="predict_proba"
    )[:, 1]
    reg_oof = cross_val_predict(regression_model, x_features, y_regression, groups=groups, cv=cv)
    reg_oof = np.clip(reg_oof, a_min=0.0, a_max=None)

    report = pd.DataFrame(
        {
            "date": x_frame["measured_on"],
            "year": groups,
            "actual_quality_bad": y_quality,
            "pred_quality_bad": cls_oof,
            "pred_bad_probability": cls_oof_proba,
            "actual_enterococci": y_regression["enterococci"],
            "pred_enterococci": reg_oof[:, 0],
            "actual_ecoli": y_regression["ecoli"],
            "pred_ecoli": reg_oof[:, 1],
        }
    )
    report["date"] = report["date"].astype(str)
    report["enterococci_abs_error"] = (report["actual_enterococci"] - report["pred_enterococci"]).abs()
    report["ecoli_abs_error"] = (report["actual_ecoli"] - report["pred_ecoli"]).abs()

    warning_pred = (cls_oof_proba >= WARNING_PROBABILITY_THRESHOLD).astype(int)

    by_year: dict[str, object] = {}
    for year in sorted(report["year"].unique()):
        year_frame = report[report["year"] == year]
        by_year[str(year)] = {
            "rows": int(len(year_frame)),
            "accuracy": float(accuracy_score(year_frame["actual_quality_bad"], year_frame["pred_quality_bad"])),
            "f1": float(f1_score(year_frame["actual_quality_bad"], year_frame["pred_quality_bad"], zero_division=0)),
            "enterococci_mae": float(
                mean_absolute_error(year_frame["actual_enterococci"], year_frame["pred_enterococci"])
            ),
            "ecoli_mae": float(mean_absolute_error(year_frame["actual_ecoli"], year_frame["pred_ecoli"])),
        }

    return {
        "rows": int(len(x_frame)),
        "years": [int(year) for year in sorted(groups.unique())],
        "bad_count": int(y_quality.sum()),
        "good_count": int((1 - y_quality).sum()),
        "logo_accuracy": float(accuracy_score(y_quality, cls_oof)),
        "logo_f1": float(f1_score(y_quality, cls_oof)),
        "warning_threshold": WARNING_PROBABILITY_THRESHOLD,
        "warning_accuracy": float(accuracy_score(y_quality, warning_pred)),
        "warning_precision": float(precision_score(y_quality, warning_pred, zero_division=0)),
        "warning_recall": float(recall_score(y_quality, warning_pred, zero_division=0)),
        "enterococci_mae": float(mean_absolute_error(y_regression["enterococci"], reg_oof[:, 0])),
        "ecoli_mae": float(mean_absolute_error(y_regression["ecoli"], reg_oof[:, 1])),
        "enterococci_rmse": float(np.sqrt(mean_squared_error(y_regression["enterococci"], reg_oof[:, 0]))),
        "ecoli_rmse": float(np.sqrt(mean_squared_error(y_regression["ecoli"], reg_oof[:, 1]))),
        "enterococci_r2": float(r2_score(y_regression["enterococci"], reg_oof[:, 0])),
        "ecoli_r2": float(r2_score(y_regression["ecoli"], reg_oof[:, 1])),
        "per_year": by_year,
        "worst_enterococci_rows": report.sort_values("enterococci_abs_error", ascending=False)
        .head(8)
        .to_dict(orient="records"),
        "worst_ecoli_rows": report.sort_values("ecoli_abs_error", ascending=False)
        .head(8)
        .to_dict(orient="records"),
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

    regression_model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
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


def load_artifacts(models_dir: Path) -> tuple[LogisticRegression, object, dict[str, object]]:
    with (models_dir / "classification.pkl").open("rb") as handle:
        classification_model = pickle.load(handle)
    with (models_dir / "regression.pkl").open("rb") as handle:
        regression_model = pickle.load(handle)
    metadata = json.loads((models_dir / "metadata.json").read_text())
    return classification_model, regression_model, metadata


def generate_predictions(
    weather_records: list[dict[str, object]],
    *,
    timezone,
    models_dir: Path,
    after_feature_time_local: pd.Timestamp | None = None,
) -> list[dict[str, object]]:
    classification_model, regression_model, metadata = load_artifacts(models_dir)
    current_features = build_prediction_feature_rows(
        weather_records,
        timezone=timezone,
        after_feature_time_local=after_feature_time_local,
    )
    if current_features.empty:
        return []
    feature_columns = metadata["feature_columns"]
    feature_vector = current_features[feature_columns]
    probabilities = classification_model.predict_proba(feature_vector)
    regression_outputs = regression_model.predict(feature_vector)
    regression_outputs = np.clip(regression_outputs, a_min=0.0, a_max=None)

    predictions: list[dict[str, object]] = []
    for index, feature_time_local in enumerate(feature_vector.index):
        probability_bad = float(probabilities[index][1])
        enterococci_predicted, ecoli_predicted = regression_outputs[index]
        predictions.append(
            {
                "feature_spec_version": metadata["feature_spec_version"],
                "feature_snapshot": {
                    key: float(value) for key, value in feature_vector.iloc[index].to_dict().items()
                },
                "predicted_at": feature_time_local.isoformat(),
                "predicted_for_date": feature_time_local.date().isoformat(),
                "feature_time_local": feature_time_local.isoformat(),
                "quality_probability_bad": probability_bad,
                "quality_label_predicted": prediction_band_from_probability(probability_bad),
                "enterococci_predicted": float(enterococci_predicted),
                "ecoli_predicted": float(ecoli_predicted),
            }
        )
    return predictions
