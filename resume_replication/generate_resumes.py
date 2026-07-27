"""Generate the full resume replication set.

15 names x 2 majors x 2 quant levels x 2 volunteer levels x 2 course-rigor
levels x 2 EC-strength levels = 480 resumes, written as .txt files plus a
manifest.csv logging every factor level per file (needed later to regress
letter language back onto candidate factors).
"""

import csv
import itertools
from pathlib import Path

import content_bank as cb

HERE = Path(__file__).parent
NAME_MAPPING_CSV = HERE.parent / "name mapping -CAV.csv"
TEMPLATE_PATH = HERE / "resume_template.txt"
OUTPUT_DIR = HERE / "resumes"

MAJORS = ["CS", "English"]
LEVELS = ["high", "low"]
LEVEL_CODE = {"high": "H", "low": "L"}

PRONOUNS = {
    "Female": "she/her",
    "Male": "he/him",
    "Nonbinary": "they/them",
}


def load_names(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def build_fields(name_row, major, quant, volunteer, rigor, ec):
    fields = {
        "name": name_row["student_name"],
        "pronouns": PRONOUNS[name_row["gender_identity"]],
        "major_label": cb.MAJOR_LABELS[major],
        "high_school": cb.HIGH_SCHOOL,
        "research": cb.RESEARCH,
        "internship": cb.INTERNSHIP,
    }
    fields.update(cb.QUANT[quant])
    fields.update(cb.VOLUNTEER[volunteer])
    fields.update(cb.RIGOR[major][rigor])
    fields.update(cb.EC[major][ec])
    return fields


def main():
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    names = load_names(NAME_MAPPING_CSV)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = []
    combos = itertools.product(names, MAJORS, LEVELS, LEVELS, LEVELS, LEVELS)
    for name_row, major, quant, volunteer, rigor, ec in combos:
        fields = build_fields(name_row, major, quant, volunteer, rigor, ec)
        resume_text = template.format(**fields)

        code = "".join(LEVEL_CODE[lvl] for lvl in (quant, volunteer, rigor, ec))
        filename = f"resume_{int(name_row['name_id']):02d}_{major}_{code}.txt"
        (OUTPUT_DIR / filename).write_text(resume_text, encoding="utf-8")

        manifest.append({
            "filename": filename,
            "name_id": name_row["name_id"],
            "student_name": name_row["student_name"],
            "racial_group": name_row["racial_group"],
            "gender_identity": name_row["gender_identity"],
            "pronouns": fields["pronouns"],
            "major": major,
            "quant_level": quant,
            "volunteer_level": volunteer,
            "rigor_level": rigor,
            "ec_level": ec,
        })

    manifest_path = OUTPUT_DIR / "manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
        writer.writeheader()
        writer.writerows(manifest)

    print(f"Wrote {len(manifest)} resumes to {OUTPUT_DIR}/ (manifest.csv written)")


if __name__ == "__main__":
    main()
