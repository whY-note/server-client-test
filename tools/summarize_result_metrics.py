#!/usr/bin/env python3
"""Aggregate selected metrics from result CSV files into one summary CSV.

Default behavior matches the manual processing done in this workspace:
- Input directory: ./result
- Find all *.csv recursively
- Skip the output file itself to avoid self-inclusion
- Keep only the required identity columns and key metrics
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Tuple


REQUIRED_COLUMNS = [
    "user_name",
    "protocol",
    "packaging_type",
    "is_jpeg",
    "avg_RTT",
    "p95_RTT",
    "max_RTT",
    "timeout_count",
    "action_success_rate",
    "fps",
    "avg_step_time",
    "goodput_mbps",
    "wire_goodput_mbps",
    "avg_total_wire_bytes_est",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize selected metrics from result CSV files."
    )
    parser.add_argument(
        "--input-dir",
        default="result",
        help="Directory to recursively search for CSV files (default: result)",
    )
    parser.add_argument(
        "--output",
        default="result/summary_metrics.csv",
        help="Output summary CSV path (default: result/summary_metrics.csv)",
    )
    return parser.parse_args()


def collect_csv_files(input_dir: Path, output_path: Path) -> List[Path]:
    files = sorted(input_dir.rglob("*.csv"))
    output_resolved = output_path.resolve()
    return [f for f in files if f.resolve() != output_resolved]


def summarize(csv_files: List[Path], output_path: Path) -> Tuple[int, int]:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    file_count = 0
    row_count = 0
    with output_path.open("w", newline="", encoding="utf-8") as out_fp:
        writer = csv.DictWriter(out_fp, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()

        for csv_path in csv_files:
            with csv_path.open("r", newline="", encoding="utf-8") as in_fp:
                reader = csv.DictReader(in_fp)
                if reader.fieldnames is None:
                    print(f"[WARN] Empty or invalid CSV header: {csv_path}", file=sys.stderr)
                    continue

                missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
                if missing:
                    missing_str = ", ".join(missing)
                    print(
                        f"[WARN] Skip {csv_path}: missing columns: {missing_str}",
                        file=sys.stderr,
                    )
                    continue

                for row in reader:
                    writer.writerow({col: row.get(col, "") for col in REQUIRED_COLUMNS})
                    row_count += 1
                file_count += 1

    return file_count, row_count


def main() -> int:
    args = parse_args()

    input_dir = Path(args.input_dir)
    output_path = Path(args.output)

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"[ERROR] Input directory not found: {input_dir}", file=sys.stderr)
        return 1

    csv_files = collect_csv_files(input_dir, output_path)
    if not csv_files:
        print(f"[ERROR] No CSV files found under: {input_dir}", file=sys.stderr)
        return 1

    used_files, total_rows = summarize(csv_files, output_path)

    print(f"Wrote: {output_path}")
    print(f"Source CSV files used: {used_files}")
    print(f"Summary rows (excluding header): {total_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
