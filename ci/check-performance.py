"""Fail the CI build when JMeter reported request or assertion failures."""
import csv
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python ci/check-performance.py reports/performance.jtl")
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"JMeter report missing: {path}")
        return 2
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or "success" not in reader.fieldnames:
            print("Expected JMeter CSV with 'success' column.")
            return 2
        rows = list(reader)
    if not rows:
        print("JMeter didn't execute any samples.")
        return 1
    failed = sum(1 for r in rows if r.get("success", "").lower() != "true")
    print(f"JMeter: {len(rows)} samples, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
