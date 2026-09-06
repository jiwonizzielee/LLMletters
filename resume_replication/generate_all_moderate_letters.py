"""Generate a moderate recommendation letter for each of the 480 replicated resumes."""
import concurrent.futures
import csv
import sys
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generate_letters import DEFAULT_MODEL, build_prompt, generate_letter, write_docx

RESUMES_DIR = Path(__file__).resolve().parent / "resumes"
MANIFEST = RESUMES_DIR / "manifest.csv"
TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "prompt_template_moderate_teacher.txt"
OUTPUT_DIR = Path.home() / "Desktop" / "generated_letters_moderate_480"
EFFORT = "medium"
MAX_WORKERS = 6
MAX_RETRIES = 5


def process(row, client, template):
    filename = row["filename"]
    name = row["student_name"]
    resume_text = (RESUMES_DIR / filename).read_text(encoding="utf-8")
    prompt = build_prompt(template, name, resume_text)

    for attempt in range(MAX_RETRIES):
        try:
            letter = generate_letter(client, DEFAULT_MODEL, EFFORT, prompt)
            break
        except anthropic.RateLimitError:
            time.sleep(2 ** attempt * 2)
        except Exception as e:
            return filename, None, f"{type(e).__name__}: {e}"
    else:
        return filename, None, "rate limited after retries"

    out_name = Path(filename).stem + ".docx"
    write_docx(letter, OUTPUT_DIR / out_name)
    return filename, out_name, None


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    client = anthropic.Anthropic()

    with open(MANIFEST, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    results, failures = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(process, row, client, template): row for row in rows}
        for done, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            row = futures[fut]
            filename, out_name, err = fut.result()
            if err:
                print(f"[{done}/{len(rows)}] FAILED {filename}: {err}", file=sys.stderr)
                failures.append({**row, "error": err})
            else:
                print(f"[{done}/{len(rows)}] wrote {out_name}")
                results.append({**row, "letter_filename": out_name})

    fields = list(rows[0].keys()) + ["letter_filename"]
    with open(OUTPUT_DIR / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    if failures:
        fail_fields = list(rows[0].keys()) + ["error"]
        with open(OUTPUT_DIR / "failures.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fail_fields)
            writer.writeheader()
            writer.writerows(failures)

    print(f"\nDone: {len(results)}/{len(rows)} letters written to {OUTPUT_DIR}")
    if failures:
        print(f"Failures: {len(failures)} (see failures.csv)", file=sys.stderr)


if __name__ == "__main__":
    main()
