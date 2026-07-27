"""Batch-generate recommendation letters across the full resume set.

For every resume in resume_replication/resumes/, generates letters under
both strength conditions (prompt_template.txt = strong, prompt_template_weak.txt
= weak), with N replications each, so letter language can be regressed against
every manipulated factor (race, gender, pronouns, major, quant/volunteer/rigor/ec
level, and letter strength) plus replication noise.
"""

import argparse
import csv
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic

HERE = Path(__file__).parent
DEFAULT_RESUMES_DIR = HERE / "resume_replication" / "resumes"
DEFAULT_MANIFEST = DEFAULT_RESUMES_DIR / "manifest.csv"
DEFAULT_MODEL = "claude-opus-4-8"

STRENGTH_TEMPLATES = {
    "strong": HERE / "prompt_template.txt",
    "weak": HERE / "prompt_template_weak.txt",
}


def load_manifest(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def generate_letter(client, model, effort, template, candidate_name, resume_text):
    prompt = template.format(candidate_name=candidate_name, resume_text=resume_text)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        output_config={"effort": effort},
        messages=[{"role": "user", "content": prompt}],
    )
    return next(b.text for b in response.content if b.type == "text")


def build_jobs(manifest_rows, resumes_dir, strengths, replications, limit):
    rows = manifest_rows[:limit] if limit else manifest_rows
    jobs = []
    for row in rows:
        resume_path = resumes_dir / row["filename"]
        for strength in strengths:
            for rep in range(1, replications + 1):
                jobs.append({**row, "resume_path": resume_path, "strength": strength, "replication": rep})
    return jobs


def run_job(client, model, effort, templates, job, output_dir):
    resume_text = job["resume_path"].read_text(encoding="utf-8")
    template = templates[job["strength"]]
    letter_text = generate_letter(
        client, model, effort, template, job["student_name"], resume_text
    )

    stem = job["resume_path"].stem  # e.g. resume_01_CS_HHHH
    out_name = f"{stem}_{job['strength']}_rep{job['replication']:02d}.txt"
    (output_dir / out_name).write_text(letter_text, encoding="utf-8")
    return {**{k: v for k, v in job.items() if k != "resume_path"}, "filename": out_name}


def main():
    parser = argparse.ArgumentParser(
        description="Batch-generate recommendation letters (strong/weak x N replications) "
        "for every resume in the resume replication set."
    )
    parser.add_argument("--resumes-dir", default=str(DEFAULT_RESUMES_DIR))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output-dir", default="generated_letters_batch")
    parser.add_argument(
        "--strengths", nargs="+", choices=["strong", "weak"], default=["strong", "weak"]
    )
    parser.add_argument("--replications", type=int, default=10)
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Only use the first N resumes from the manifest (for dry runs)",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"]
    )
    parser.add_argument("--workers", type=int, default=5, help="Concurrent API requests")
    args = parser.parse_args()

    resumes_dir = Path(args.resumes_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    templates = {k: v.read_text(encoding="utf-8") for k, v in STRENGTH_TEMPLATES.items()}
    manifest_rows = load_manifest(args.manifest)
    jobs = build_jobs(manifest_rows, resumes_dir, args.strengths, args.replications, args.limit)

    print(f"Generating {len(jobs)} letters ({args.workers} concurrent workers)...")

    client = anthropic.Anthropic()
    results = []
    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(run_job, client, args.model, args.effort, templates, job, output_dir): job
            for job in jobs
        }
        for i, future in enumerate(as_completed(futures), 1):
            job = futures[future]
            label = f"{job['filename']} [{job['strength']} rep{job['replication']}]"
            try:
                results.append(future.result())
                print(f"[{i}/{len(jobs)}] wrote {label}")
            except Exception as e:
                print(f"[{i}/{len(jobs)}] FAILED {label} ({type(e).__name__}): {e}", file=sys.stderr)
                failures.append(label)

    manifest_path = output_dir / "manifest.csv"
    if results:
        fieldnames = list(results[0].keys())
        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

    print(f"\nDone. {len(results)}/{len(jobs)} letters written to {output_dir}/ (manifest.csv written)")
    if failures:
        print(f"Failed: {len(failures)}", file=sys.stderr)


if __name__ == "__main__":
    main()
