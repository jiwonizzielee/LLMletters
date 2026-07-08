
import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_DICT_PATH = Path(__file__).parent / "dictionary_v3.csv"
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")


def load_dictionary(path):
    categories = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if not row or not row[0].strip():
                continue
            name = row[0].strip()
            patterns = [w.strip().lower() for w in row[1:] if w.strip()]
            exact = {p for p in patterns if not p.endswith("*")}
            prefixes = [p[:-1] for p in patterns if p.endswith("*")]
            categories[name] = {"exact": exact, "prefixes": prefixes}
    return categories


def tokenize(text):
    return [t.lower() for t in TOKEN_RE.findall(text)]


def count_categories(text, categories):
    tokens = tokenize(text)
    results = {}
    for name, spec in categories.items():
        matched = Counter()
        for tok in tokens:
            if tok in spec["exact"]:
                matched[tok] += 1
                continue
            for prefix in spec["prefixes"]:
                if tok.startswith(prefix):
                    matched[tok] += 1
                    break
        results[name] = {"count": sum(matched.values()), "words": matched}
    return results, len(tokens)


def print_report(results, total_words):
    name_width = max(len(n) for n in results) + 2
    print(f"Total words in letter: {total_words}\n")
    print(f"{'Category':<{name_width}}{'Count':>7}   Matched words (with frequency)")
    print("-" * 70)
    for name, data in results.items():
        top = ", ".join(f"{w}×{c}" if c > 1 else w for w, c in data["words"].most_common())
        print(f"{name:<{name_width}}{data['count']:>7}   {top}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("letter", nargs="?", help="Path to letter text file (omit to read stdin)")
    parser.add_argument("--dict", default=str(DEFAULT_DICT_PATH), help="Path to dictionary CSV")
    args = parser.parse_args()

    categories = load_dictionary(args.dict)

    if args.letter:
        text = Path(args.letter).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    results, total_words = count_categories(text, categories)
    print_report(results, total_words)


if __name__ == "__main__":
    main()
