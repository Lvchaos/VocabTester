import json
from pathlib import Path

SETS_DIR = Path(__file__).parent / "sets"

def validate_set(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))

    # Required keys
    for k in ("title", "word_bank", "question_bank"):
        if k not in data:
            raise ValueError(f"{path.name}: missing '{k}'")

    word_bank = data["word_bank"]
    qb = data["question_bank"]

    if not isinstance(word_bank, list):
        raise ValueError(f"{path.name}: word_bank must be a list")
    if not isinstance(qb, dict):
        raise ValueError(f"{path.name}: question_bank must be a dict/object")

    # Word bank checks
    if len(word_bank) != 50:
        raise ValueError(f"{path.name}: word_bank must have 50 words (got {len(word_bank)})")
    if len(set(word_bank)) != len(word_bank):
        raise ValueError(f"{path.name}: word_bank has duplicates")

    # Question bank checks
    if len(qb) != 25:
        raise ValueError(f"{path.name}: question_bank must have 25 questions (got {len(qb)})")

    # Keys must exist in word_bank
    missing = [w for w in qb.keys() if w not in word_bank]
    if missing:
        raise ValueError(f"{path.name}: question_bank keys not in word_bank: {missing}")

    # Sentence formatting checks
    for w, s in qb.items():
        if s.count("_____") != 1:
            raise ValueError(f"{path.name}: '{w}' prompt must contain exactly one '_____'")
        if w.lower() in s.lower().replace("_____", ""):
            raise ValueError(f"{path.name}: '{w}' appears in its own sentence (leaks answer)")

    return True

def main():
    paths = sorted(SETS_DIR.glob("*.json"))
    if not paths:
        print("No sets found.")
        return

    titles = {}
    for p in paths:
        validate_set(p)
        title = json.loads(p.read_text(encoding="utf-8")).get("title", p.stem)
        if title in titles:
            raise ValueError(f"Duplicate title: '{title}' in {titles[title]} and {p.name}")
        titles[title] = p.name

    print(f"OK: validated {len(paths)} set(s).")

if __name__ == "__main__":
    main()
