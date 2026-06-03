"""Eval runner: tests rule-based risk detection against the dataset.

This evaluates only the deterministic (rule-based) part of the pipeline.
LLM-based agent evaluations should be run separately with an API key.

Usage:
    uv run python -m evals.run_evals
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from src.agents.risk import _check_rules
from src.tools.financials import fetch_financials


async def run_eval(ticker: str, expected_categories: list[str]) -> dict:
    """Run eval for a single ticker."""
    try:
        financials = await fetch_financials(ticker)
    except Exception as exc:
        return {
            "ticker": ticker,
            "status": "error",
            "error": str(exc),
            "expected": expected_categories,
            "found": [],
        }

    flags = _check_rules(financials.model_dump())
    found_categories = list({f.category for f in flags})

    # Check: did we find flags in at least the expected categories?
    expected_set = set(expected_categories)
    found_set = set(found_categories)
    missed = expected_set - found_set
    extra = found_set - expected_set

    return {
        "ticker": ticker,
        "status": "pass" if not missed else "partial",
        "expected": sorted(expected_categories),
        "found": sorted(found_categories),
        "missed": sorted(missed),
        "extra": sorted(extra),
        "flag_count": len(flags),
    }


async def main() -> None:
    dataset_path = Path(__file__).parent / "dataset.json"
    with open(dataset_path) as f:
        dataset = json.load(f)

    print(f"\nRunning evals on {len(dataset)} companies...\n")
    print(f"{'Ticker':<8} {'Status':<10} {'Expected':<30} {'Found':<30} {'Missed':<20}")
    print("-" * 100)

    results = []
    passed = 0
    partial = 0
    errors = 0

    for entry in dataset:
        result = await run_eval(entry["ticker"], entry["expected_risk_categories"])
        results.append(result)

        status_marker = {"pass": "OK", "partial": "MISS", "error": "ERR"}.get(
            result["status"], "?"
        )
        print(
            f"{result['ticker']:<8} {status_marker:<10} "
            f"{', '.join(result['expected']):<30} "
            f"{', '.join(result['found']):<30} "
            f"{', '.join(result.get('missed', [])):<20}"
        )

        if result["status"] == "pass":
            passed += 1
        elif result["status"] == "partial":
            partial += 1
        else:
            errors += 1

    total = len(results)
    print(f"\n{'=' * 100}")
    print(f"Results: {passed}/{total} pass | {partial}/{total} partial | {errors}/{total} errors")
    print(f"Accuracy: {passed / total:.1%}" if total else "No data")

    # Save results
    output_path = Path(__file__).parent / "results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
