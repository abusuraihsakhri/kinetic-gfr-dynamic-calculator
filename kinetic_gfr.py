#!/usr/bin/env python3
"""Chen (2013) kinetic estimated GFR for changing serum creatinine.

No third-party dependencies. This is an educational estimate, not an AKI stage,
a measured GFR, or an independent medication-dosing recommendation.
"""
import argparse
import csv
import json
import math
from pathlib import Path

MG_DL_PER_UMOL_L = 1.0 / 88.4
REQUIRED_COLUMNS = (
    "steady_state_creatinine", "baseline_gfr", "creatinine_1",
    "creatinine_2", "hours",
)


def calculate_metrics(
    *, steady_state_creatinine, baseline_gfr, creatinine_1, creatinine_2,
    hours, max_creatinine_rise_per_day=1.5, unit="mg/dL",
):
    """Estimate kinetic clearance using Chen's algebraic equation.

    All creatinine inputs use the chosen unit; max rise is in mg/dL/day.
    baseline_gfr must be paired with steady_state_creatinine, and its unit
    (mL/min or mL/min/1.73 m²) is retained in the output.
    """
    if unit not in ("mg/dL", "umol/L"):
        raise ValueError("unit must be 'mg/dL' or 'umol/L'")
    values = {
        "steady_state_creatinine": steady_state_creatinine,
        "baseline_gfr": baseline_gfr,
        "creatinine_1": creatinine_1,
        "creatinine_2": creatinine_2,
        "hours": hours,
        "max_creatinine_rise_per_day": max_creatinine_rise_per_day,
    }
    numbers = {}
    for name, value in values.items():
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be a finite positive number") from exc
        if not math.isfinite(number) or number <= 0:
            raise ValueError(f"{name} must be a finite positive number")
        numbers[name] = number

    factor = MG_DL_PER_UMOL_L if unit == "umol/L" else 1.0
    steady = numbers["steady_state_creatinine"] * factor
    scr1 = numbers["creatinine_1"] * factor
    scr2 = numbers["creatinine_2"] * factor
    delta = scr2 - scr1
    mean = (scr1 + scr2) / 2
    correction = 1 - 24 * delta / (
        numbers["hours"] * numbers["max_creatinine_rise_per_day"]
    )
    if correction < -1e-12:
        raise ValueError(
            "Observed creatinine rise exceeds the selected maximum anuric rise. "
            "The model yields a negative clearance; reconsider assumptions."
        )
    correction = max(0.0, correction)
    kegfr = steady * numbers["baseline_gfr"] / mean * correction
    if not math.isfinite(kegfr):
        raise ValueError("Calculation exceeds the supported numeric range")
    return {
        "kegfr": round(kegfr, 2),
        "mean_creatinine": round(mean / factor, 4),
        "creatinine_change": round(delta / factor, 4),
        "change_per_day": round(24 * delta / numbers["hours"] / factor, 4),
        "kinetic_factor": round(correction, 6),
        "creatinine_unit": unit,
        "clearance_unit": "same as baseline_gfr",
        "method": "Chen 2013 kinetic GFR",
        "warning": (
            "Research/educational estimate only. Not an AKI stage or measured "
            "GFR. Assumes stable creatinine generation/distribution volume. "
            "Verify the baseline clearance and its normalization before use."
        ),
    }


def process_batch(input_csv: str, output_csv: str) -> int:
    """Convert a CSV of clinical inputs to KeGFR results; fail on invalid rows."""
    source, target = Path(input_csv), Path(output_csv)
    if not source.is_file():
        raise FileNotFoundError(f"Input CSV not found: {source}")
    if source.resolve() == target.resolve():
        raise ValueError("Input and output paths must differ")
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        missing = set(REQUIRED_COLUMNS) - set(headers)
        if missing:
            raise ValueError("Missing CSV columns: " + ", ".join(sorted(missing)))
        if len(set(headers)) != len(headers):
            raise ValueError("Duplicate CSV column headers")
        results = []
        for line, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"CSV row {line}: incorrect column count")
            try:
                result = calculate_metrics(
                    **{name: row[name] for name in REQUIRED_COLUMNS},
                    max_creatinine_rise_per_day=(
                        row.get("max_creatinine_rise_per_day") or 1.5
                    ),
                    unit=row.get("unit") or "mg/dL",
                )
            except ValueError as exc:
                raise ValueError(f"CSV row {line}: {exc}") from exc
            # Escape spreadsheet formulas in untrusted pass-through columns.
            sanitized = {
                key: ("'" + val if val.lstrip().startswith(("=", "+", "-", "@")) else val)
                for key, val in row.items()
            }
            results.append({
                **sanitized, "kegfr": result["kegfr"],
                "kinetic_factor": result["kinetic_factor"],
            })
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=[*headers, "kegfr", "kinetic_factor"]
        )
        writer.writeheader()
        writer.writerows(results)
    return len(results)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Chen kinetic GFR estimate; educational/research use only"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("single", help="Estimate KeGFR for one interval")
    one.add_argument("--steady-state-creatinine", type=float, required=True)
    one.add_argument("--baseline-gfr", type=float, required=True)
    one.add_argument("--creatinine-1", type=float, required=True)
    one.add_argument("--creatinine-2", type=float, required=True)
    one.add_argument("--hours", type=float, required=True)
    one.add_argument("--max-creatinine-rise-per-day", type=float, default=1.5)
    one.add_argument("--unit", choices=["mg/dL", "umol/L"], default="mg/dL")
    batch = commands.add_parser("batch", help="Estimate KeGFR for a CSV")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            values = vars(args).copy()
            values.pop("command")
            print(json.dumps(calculate_metrics(**values), indent=2))
        else:
            count = process_batch(args.input, args.output)
            print(f"Processed {count} records -> {args.output}")
    except (ValueError, FileNotFoundError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
