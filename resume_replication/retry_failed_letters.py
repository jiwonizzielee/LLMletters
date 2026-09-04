"""Retry the resumes that failed in the last generate_all_strong_letters.py run."""
import concurrent.futures
import csv
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_all_strong_letters import MAX_WORKERS, OUTPUT_DIR, TEMPLATE_PATH, process

FAILURES_PATH = OUTPUT_DIR / "failures.csv"
MANIFEST_PATH = OUTPUT_DIR / "manifest.csv"


def main():
    if not FAILURES_PATH.exists():
        print("No failures.csv found, nothing to retry.")
        return

    with open(FAILURES_PATH, newline="", encoding="utf-8-sig") as f:
        retry_rows = list(csv.DictReader(f))
    retry_rows = [{k: v for k, v in row.items() if k != "error"} for row in retry_rows]

    if not retry_rows:
        print("failures.csv is empty, nothing to retry.")
        return

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    client = anthropic.Anthropic()

    results, failures = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(process, row, client, template): row for row in retry_rows}
        for done, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            row = futures[fut]
            filename, out_name, err = fut.result()
            if err:
                print(f"[{done}/{len(retry_rows)}] FAILED {filename}: {err}", file=sys.stderr)
                failures.append({**row, "error": err})
            else:
                print(f"[{done}/{len(retry_rows)}] wrote {out_name}")
                results.append({**row, "letter_filename": out_name})

    # merge newly successful rows into the existing manifest.csv
    with open(MANIFEST_PATH, newline="", encoding="utf-8-sig") as f:
        existing = list(csv.DictReader(f))
    fields = list(existing[0].keys()) if existing else list(results[0].keys())
    combined = existing + results
    with open(MANIFEST_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(combined)

    # rewrite failures.csv with only the rows that failed again
    if failures:
        fail_fields = list(retry_rows[0].keys()) + ["error"]
        with open(FAILURES_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fail_fields)
            writer.writeheader()
            writer.writerows(failures)
    else:
        FAILURES_PATH.unlink()

    print(f"\nDone: {len(results)}/{len(retry_rows)} retried letters written to {OUTPUT_DIR}")
    if failures:
        print(f"Still failing: {len(failures)} (see failures.csv)", file=sys.stderr)


if __name__ == "__main__":
    main()
