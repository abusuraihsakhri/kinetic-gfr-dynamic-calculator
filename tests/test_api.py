"""API contract tests for kinetic GFR, independent of legacy audit demos."""
from fastapi.testclient import TestClient

from agents.api import app

client = TestClient(app)


def test_kinetic_gfr_api():
    res = client.post("/api/kinetic-gfr", json={
        "steady_state_creatinine": 1,
        "baseline_gfr": 90,
        "creatinine_1": 1.8,
        "creatinine_2": 2.4,
        "hours": 24,
    })
    assert res.status_code == 200
    assert res.json()["kegfr"] == 25.71


def test_api_negative_result_rejected():
    res = client.post("/api/kinetic-gfr", json={
        "steady_state_creatinine": 1, "baseline_gfr": 90,
        "creatinine_1": 1, "creatinine_2": 5, "hours": 24,
    })
    assert res.status_code == 422
    assert "negative clearance" in res.json()["detail"]


def test_api_nonfinite_input_rejected():
    res = client.post("/api/kinetic-gfr", json={
        "steady_state_creatinine": 1, "baseline_gfr": 90,
        "creatinine_1": 1, "creatinine_2": 2,
        "hours": "NaN",
    })
    assert res.status_code == 422


def test_api_health():
    assert client.get("/health").status_code == 200
