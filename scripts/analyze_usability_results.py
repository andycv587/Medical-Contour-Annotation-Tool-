import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize usability/time-study results if real rows exist.")
    parser.add_argument("--input", default="forms/usability_results_template.csv")
    parser.add_argument("--output", default="results/usability")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    path = Path(args.input)
    if not path.exists():
        _not_run(out, f"input file does not exist: {path}")
        return 2
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    real_rows = [row for row in rows if str(row.get("status", "")).upper() not in {"NOT_RUN", "", "TO_BE_FILLED"}]
    if not real_rows:
        _not_run(out, "no completed usability rows found")
        return 2
    conditions = sorted({row.get("condition", "") for row in real_rows})
    with open(out / "usability_summary.md", "w", encoding="utf-8") as f:
        f.write("# Usability Summary\n\n")
        f.write("This summary includes only rows marked as completed in the input CSV.\n\n")
        f.write(f"- Completed rows: {len(real_rows)}\n")
        f.write("- Conditions: " + ", ".join(conditions) + "\n")
    return 0


def _not_run(out: Path, reason: str) -> None:
    (out / "USABILITY_NOT_RUN.md").write_text(
        "# Usability Analysis Not Run\n\n"
        f"{reason}\n\n"
        "No user-study results were generated or fabricated.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
