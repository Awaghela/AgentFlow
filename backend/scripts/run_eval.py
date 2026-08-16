"""
Triggers a new run of the eval suite against whatever scenarios are
already seeded in the database, and prints a category-by-category summary.

Run with:  python -m scripts.run_eval
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collections import defaultdict

from app.db.session import SessionLocal
from app.eval.runner import run_eval_suite
from app.models.eval import EvalScenario


def main() -> None:
    db = SessionLocal()
    try:
        scenarios = db.query(EvalScenario).order_by(EvalScenario.category, EvalScenario.name).all()
        if not scenarios:
            print("No scenarios found. Run `python -m scripts.seed_db` first.")
            return

        run = run_eval_suite(db, scenarios, label="manual CLI run")

        by_category = defaultdict(lambda: [0, 0])
        for result in run.results:
            idx = 0 if result.passed else 1
            by_category[result.category][idx] += 1

        print(f"\nEval run {run.id} — {run.passed_count}/{run.scenario_count} passed\n")
        print(f"{'category':<24} {'passed':>8} {'failed':>8}")
        for category, (passed, failed) in sorted(by_category.items()):
            print(f"{category:<24} {passed:>8} {failed:>8}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
