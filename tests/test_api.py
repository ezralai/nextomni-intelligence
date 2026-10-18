"""
Unit and Integration Tests for NextOmni Analytics Intelligence FastAPI Service.
Uses FastAPI TestClient to test endpoints and schema contracts.
"""

import unittest
from fastapi.testclient import TestClient
from python_ml.llm_cognitive_service import app

class TestNextOmniApiService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "healthy")
        self.assertIn("model_loaded", payload)

    def test_burnout_prediction_nominal(self):
        sample_input = {
            "user_id": "usr_test_001",
            "total_focus_min": 180.0,
            "deep_work_min": 120.0,
            "avg_flow_score": 8.0,
            "total_interruptions": 1,
            "rolling_7d_focus_min": 170.0,
            "rolling_7d_flow_score": 8.2,
            "rolling_14d_interruptions": 10,
            "sleep_hours": 7.8,
            "sleep_quality": 4.5,
            "caffeine_intake_mg": 120.0,
            "avg_daily_energy": 4.0,
            "habit_adherence_rate": 0.85,
            "rolling_7d_habit_rate": 0.88
        }
        response = self.client.post("/api/v1/predict/burnout-risk", json=sample_input)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user_id"], "usr_test_001")
        self.assertIn(data["risk_tier"], ["LOW", "MODERATE", "CRITICAL"])
        self.assertIsInstance(data["burnout_probability"], float)
        self.assertIn("prescriptive_action", data)

    def test_cognitive_debrief_analysis(self):
        sample_input = {
            "user_id": "usr_test_001",
            "journal_text": "Today felt like a total failure and impossible to finish.",
            "mood_score": 2,
            "energy_level": 2.0
        }
        response = self.client.post("/api/v1/cognitive/debrief", json=sample_input)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["sentiment_polarity"], "negative")
        self.assertGreater(len(data["detected_distortions"]), 0)
        self.assertIn("mentorship_feedback", data)

    def test_weekly_digest_synthesis(self):
        sample_input = {
            "user_id": "usr_test_001",
            "week_start_date": "2026-10-01",
            "total_focus_hours": 24.5,
            "deep_work_percentage": 62.0,
            "habit_completion_rate": 80.0,
            "urgent_tasks_completed": 5,
            "urgent_tasks_missed": 0
        }
        response = self.client.post("/api/v1/telemetry/digest", json=sample_input)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("executive_summary", data)
        self.assertGreater(len(data["key_achievements"]), 0)
        self.assertIsInstance(data["prescriptive_sprint_adjustments"], list)

if __name__ == "__main__":
    unittest.main()
