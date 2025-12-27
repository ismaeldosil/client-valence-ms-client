#!/usr/bin/env python3
"""Find code without tests and suggest what to test.

This script runs pytest with coverage and identifies files
with low coverage, showing which lines are missing tests.

Usage:
    python scripts/find_untested_code.py
    # or
    make find-gaps
"""
import subprocess
import json
import sys
from pathlib import Path


def find_untested(threshold: int = 70) -> int:
    """Find files with coverage below threshold.

    Args:
        threshold: Minimum coverage percentage (default 70%)

    Returns:
        Exit code (0 if all files above threshold, 1 otherwise)
    """
    # Run coverage and get JSON report
    print("Running tests with coverage...")
    result = subprocess.run(
        [
            "pytest",
            "--cov=src",
            "--cov-report=json",
            "-q",
            "--tb=no",
        ],
        capture_output=True,
        text=True,
    )

    # Check if coverage.json was created
    coverage_file = Path("coverage.json")
    if not coverage_file.exists():
        print("Error: coverage.json not found. Make sure pytest-cov is installed.")
        print(f"pytest output: {result.stderr}")
        return 1

    with open(coverage_file) as f:
        data = json.load(f)

    # Get totals
    totals = data.get("totals", {})
    total_coverage = totals.get("percent_covered", 0)

    print(f"\n{'=' * 60}")
    print(f"  Total Coverage: {total_coverage:.1f}%")
    print(f"  Threshold: {threshold}%")
    print(f"{'=' * 60}\n")

    # Find files below threshold
    low_coverage_files = []
    for file_path, info in data.get("files", {}).items():
        coverage = info.get("summary", {}).get("percent_covered", 0)
        if coverage < threshold:
            missing = info.get("missing_lines", [])
            low_coverage_files.append({
                "file": file_path,
                "coverage": coverage,
                "missing": missing,
            })

    if not low_coverage_files:
        print("All files meet the coverage threshold!")
        return 0

    # Sort by coverage (lowest first)
    low_coverage_files.sort(key=lambda x: x["coverage"])

    print(f"Files below {threshold}% coverage:\n")
    for item in low_coverage_files:
        print(f"  {item['file']}: {item['coverage']:.1f}%")
        if item["missing"]:
            # Show first 10 missing lines
            missing_preview = item["missing"][:10]
            missing_str = ", ".join(str(line) for line in missing_preview)
            if len(item["missing"]) > 10:
                missing_str += f", ... (+{len(item['missing']) - 10} more)"
            print(f"    Missing lines: {missing_str}")
        print()

    print(f"\nTotal: {len(low_coverage_files)} file(s) need more tests.")
    return 1


if __name__ == "__main__":
    # Allow threshold to be passed as argument
    threshold = 70
    if len(sys.argv) > 1:
        try:
            threshold = int(sys.argv[1])
        except ValueError:
            print(f"Invalid threshold: {sys.argv[1]}")
            sys.exit(1)

    sys.exit(find_untested(threshold))
