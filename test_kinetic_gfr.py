"""Reference and failure-mode tests for Chen (2013) kinetic GFR."""
import csv
import json
import math
import pytest

from kinetic_gfr import calculate_metrics, main, process_batch

CASE = dict(
    steady_state_creatinine=1.0,
    baseline_gfr=90.0,
    creatinine_1=1.8,
    creatinine_2=2.4,
    hours=24,
)


def test_chens_rising_creatinine_example():
    result = calculate_metrics(**CASE)
    assert result["kegfr"] == pytest.approx(25.71, abs=0.01)
    assert result["kinetic_factor"] == pytest.approx(0.6)
    assert result["creatinine_change"] == pytest.approx(0.6)


def test_unchanged_creatinine():
    result = calculate_metrics(
        steady_state_creatinine=1, baseline_gfr=90,
        creatinine_1=1, creatinine_2=1, hours=24
    )
    assert result["kegfr"] == 90


def test_decreasing_creatinine():
    result = calculate_metrics(**{**CASE, "creatinine_1": 2.4, "creatinine_2": 1.8})
    assert result["kegfr"] == pytest.approx(60.0, abs=0.01)
    assert result["kinetic_factor"] == pytest.approx(1.4)


def test_units_agree():
    umol = calculate_metrics(**{
        **CASE,
        "steady_state_creatinine": 88.4,
        "creatinine_1": 1.8 * 88.4,
        "creatinine_2": 2.4 * 88.4,
        "unit": "umol/L",
    })
    assert umol["kegfr"] == calculate_metrics(**CASE)["kegfr"]


@pytest.mark.parametrize("name,bad", [
    ("hours", 0), ("hours", -2), ("baseline_gfr", -5),
    ("creatinine_1", 0), ("creatinine_2", float("nan")),
    ("steady_state_creatinine", float("inf")),
    ("max_creatinine_rise_per_day", 0), ("creatinine_1", "nonsense"),
])
def test_rejects_bad_inputs(name, bad):
    with pytest.raises(ValueError):
        calculate_metrics(**{**CASE, name: bad})


def test_nonphysical_max_rise_rejected():
    with pytest.raises(ValueError, match="negative clearance"):
        calculate_metrics(**{**CASE, "creatinine_2": 5})


def test_unit_validation():
    with pytest.raises(ValueError, match="unit"):
        calculate_metrics(**{**CASE, "unit": "mmol/L"})


def test_missing_required_params():
    with pytest.raises(TypeError):
        calculate_metrics(v1=2, v2=4)


def test_batch(tmp_path):
    source, target = tmp_path / "source.csv", tmp_path / "out.csv"
    source.write_text(
        "steady_state_creatinine,baseline_gfr,creatinine_1,creatinine_2,hours,comment\n"
        "1,90,1.8,2.4,24,example\n"
        "1,90,1,1,24,=HYPERLINK(\"https://example.com\")\n",
        encoding="utf-8"
    )
    assert process_batch(str(source), str(target)) == 2
    with target.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert float(rows[0]["kegfr"]) == pytest.approx(25.71, abs=0.01)
    assert rows[1]["comment"].startswith("'=")


def test_batch_rejects_invalid_rows_before_writing(tmp_path):
    source, target = tmp_path / "in.csv", tmp_path / "out.csv"
    source.write_text(
        "steady_state_creatinine,baseline_gfr,creatinine_1,creatinine_2,hours\n"
        "1,90,1.8,2.4,24\n1,90,1,8,24\n",
        encoding="utf-8"
    )
    with pytest.raises(ValueError, match="row 3"):
        process_batch(str(source), str(target))
    assert not target.exists()


def test_batch_missing_headers_and_overwrite(tmp_path):
    source = tmp_path / "in.csv"
    source.write_text("v1,v2\n2,3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing CSV"):
        process_batch(str(source), str(tmp_path / "out.csv"))
    with pytest.raises(ValueError, match="paths must differ"):
        process_batch(str(source), str(source))


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        process_batch("does-not-exist.csv", "results.csv")


def test_cli_single_json(capsys):
    assert main([
        "single", "--steady-state-creatinine", "1", "--baseline-gfr", "90",
        "--creatinine-1", "1.8", "--creatinine-2", "2.4", "--hours", "24"
    ]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kegfr"] == pytest.approx(25.71, abs=0.01)


def test_cli_validation(capsys):
    with pytest.raises(SystemExit) as exc:
        main([
            "single", "--steady-state-creatinine", "1", "--baseline-gfr", "90",
            "--creatinine-1", "1.8", "--creatinine-2", "5", "--hours", "24"
        ])
    assert exc.value.code == 2
    assert "negative clearance" in capsys.readouterr().err
