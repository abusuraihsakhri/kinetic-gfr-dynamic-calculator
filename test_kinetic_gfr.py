import os
import pytest
from kinetic_gfr import calculate_metrics, process_batch, main


def test_kinetic_gfr_single():
    res = calculate_metrics(v1=12.0, v2=4.0)
    assert "score" in res
    assert "classification" in res
    assert res["score"] > 0


def test_kinetic_gfr_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "score" in content


def test_calculate_metrics_classification_low():
    """Score below 10 should classify as Low / Standard."""
    res = calculate_metrics(v1=5.0, v2=2.0)
    assert res["classification"] == "Low / Standard"
    assert res["clinical_recommendation"] == "Standard monitoring or negative cutoff"


def test_calculate_metrics_classification_moderate():
    """Score between 10 and 25 should classify as Moderate / Intermediate."""
    res = calculate_metrics(v1=15.0, v2=5.0)
    assert res["classification"] == "Moderate / Intermediate"
    assert res["clinical_recommendation"] == "Close observation or secondary evaluation"


def test_calculate_metrics_classification_high():
    """Score >= 25 should classify as High / Severe."""
    res = calculate_metrics(v1=30.0, v2=10.0)
    assert res["classification"] == "High / Severe"
    assert res["clinical_recommendation"] == "Urgent clinical intervention or primary positive finding"


def test_calculate_metrics_with_string_values():
    """Non-numeric values should be handled gracefully."""
    res = calculate_metrics(v1="abc", v2=5.0)
    assert res["score"] == 5.0
    # Both params are stored; only numeric ones contribute to score
    assert res["inputs_evaluated"] == 2


def test_calculate_metrics_empty():
    """Empty input should return default values."""
    res = calculate_metrics()
    assert res["score"] == 1.0
    assert res["inputs_evaluated"] == 0


def test_calculate_metrics_tool_field():
    """Result should include tool identifier."""
    res = calculate_metrics(v1=10.0)
    assert res["tool"] == "kinetic-gfr-dynamic-calculator"


def test_process_batch_file_not_found():
    """process_batch should raise FileNotFoundError for missing input."""
    with pytest.raises(FileNotFoundError):
        process_batch("nonexistent_file.csv", "output.csv")


def test_process_batch_empty_csv(tmp_path):
    """process_batch should raise ValueError for CSV with no headers."""
    csv_in = tmp_path / "empty.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("", encoding="utf-8")
    with pytest.raises(ValueError):
        process_batch(str(csv_in), str(csv_out))


def test_process_batch_creates_output_directory(tmp_path):
    """process_batch should create output directory if it doesn't exist."""
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "subdir" / "out.csv"
    csv_in.write_text("Patient,v1\nPat_001,15.0\n", encoding="utf-8")
    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()


def test_cli_single_command():
    """CLI single command should work with default args."""
    result = main(["single"])
    assert result is None  # main() returns None, prints JSON


def test_cli_batch_command(tmp_path, capsys):
    """CLI batch command should process CSV."""
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "cli_out.csv"
    csv_in.write_text("Patient,v1\nPat_001,15.0\n", encoding="utf-8")
    main(["batch", "-i", str(csv_in), "-o", str(csv_out)])
    assert csv_out.exists()
