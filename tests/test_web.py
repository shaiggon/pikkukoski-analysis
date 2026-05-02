import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.storage import connect, init_db, upsert_daily_prediction


class WebAppTests(unittest.TestCase):
    def test_health_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            connection = connect(db_path)
            init_db(connection)
            connection.execute(
                """
                INSERT INTO model_run (
                    trained_at, feature_spec_version, classification_model_type,
                    regression_model_type, metrics_json
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                ("2026-05-01T00:00:00+00:00", "spec", "LogisticRegression", "Ridge", "{}"),
            )
            upsert_daily_prediction(
                connection,
                {
                    "beach_id": "pikkukoski",
                    "predicted_for": "2026-05-01",
                    "quality_probability_bad": 0.2,
                    "quality_label_predicted": "good",
                    "enterococci_predicted": 20.0,
                    "ecoli_predicted": 40.0,
                    "feature_snapshot": {"kumpula_rain_now": 0.0},
                    "model_run_id": 1,
                    "generated_at": "2026-05-01T00:00:00+00:00",
                },
            )
            connection.close()

            with patch.dict(
                "os.environ",
                {
                    "PIKKUKOSKI_DB_PATH": str(db_path),
                    "PIKKUKOSKI_OUTPUT_DIR": str(Path(tmpdir) / "generated"),
                },
                clear=False,
            ):
                from importlib import reload
                import app.web as web_module

                reload(web_module)
                client = TestClient(web_module.app)
                response = client.get("/health")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "ok")

