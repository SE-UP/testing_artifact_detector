"""
Reachability-aware comparison of the regex baseline (cli.py) against the
Tree-sitter detector (cli2.py).

Where comp_rgx_ts.py compares the flat verdict - a test command appears somewhere
in a CMake file - this script compares against the reachability-aware one: the
command is in a file the project evaluates, and not in a macro nobody calls. The
baseline cannot express that question at all, so this is not a parity comparison
and its disagreements are not attributable to the parsing technique.

Usage:
    testing-artifact-detector-compare-deep --regex-file A.csv --ts-file B.csv
"""

from __future__ import annotations

import argparse

from .comparison import (
    Indicator,
    compare,
    load_csv,
    report_language_detection_consistency,
    write_disagreements,
)


# Same files as the baseline, but the reachability-aware verdict.
DEEP_CMAKE_INDICATORS: tuple[Indicator, ...] = (
    Indicator("has_cmake_file", "has_cmakelists", ("has_cmakelists",)),
    Indicator(
        "uses_gtest (find_package or gtest_discover_tests)",
        "uses_gtest",
        ("cmake_uses_gtest", "cmake_gtests_found"),
    ),
    Indicator("uses_catch2 (find_package)", "uses_catch2", ("cmake_uses_catch2",)),
    # has_cpp_tests is the baseline's name for its CMake test finding; despite the
    # name it has nothing to do with reading C++ sources.
    Indicator(
        "tests_found (reachable registration only)",
        "has_cpp_tests",
        ("cmake_tests_reachable",),
    ),
    Indicator("gtests_found (gtest_discover_tests)", "gtests_found", ("cmake_gtests_found",)),
)


def summarise(label: str, disagreements: list[dict]) -> tuple[int, int]:
    """
    Print the result of the comparison.

    :param label: Name of the comparison, used in the printed heading.
    :param disagreements: The rows collected by compare().
    :return: The number of real disagreements and of missing-data rows.
    """

    real = [row for row in disagreements if row["reason"] == "disagreement"]
    missing = len(disagreements) - len(real)
    print(f"\n{label}: {len(disagreements)} rows total "
          f"({len(real)} real disagreements, {missing} missing-data rows)")

    only_baseline = [row for row in real if row["baseline_value"] and not row["treesitter_value"]]
    only_ts = [row for row in real if row["treesitter_value"] and not row["baseline_value"]]
    print(f"  only baseline=True (Tree-sitter misses it): {len(only_baseline)}"
          f" -> {sorted({str(row['project_id']) for row in only_baseline})}")
    print(f"  only tree-sitter=True (baseline misses it): {len(only_ts)}"
          f" -> {sorted({str(row['project_id']) for row in only_ts})}")
    return len(real), missing


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare the regex baseline against the reachability-aware "
                    "verdict of the Tree-sitter detector."
    )
    parser.add_argument("--regex-file", required=True, help="CSV produced by the regex-based CLI (cli.py).")
    parser.add_argument("--ts-file", required=True, help="CSV produced by the Tree-sitter CLI (cli2.py).")
    parser.add_argument("--diff-out", required=False,
                        help="Optional path to write the disagreeing rows to.")
    args = parser.parse_args()

    baseline = load_csv(args.regex_file)
    treesitter = load_csv(args.ts_file)

    print(f"Baseline rows: {len(baseline)}, Tree-sitter rows: {len(treesitter)}")

    print("\n" + "=" * 70)
    print("reachability-aware CMake verdict, same files as the baseline")
    print("=" * 70)
    merged, disagreements = compare(baseline, treesitter, DEEP_CMAKE_INDICATORS)

    report_language_detection_consistency(merged)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    summarise("reachability-aware CMake", disagreements)

    write_disagreements(disagreements, args.diff_out)


if __name__ == "__main__":
    main()
