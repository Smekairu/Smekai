"""Обновить карточки открытого календаря MAX: python scripts/build_public_answers.py."""
import argparse
import json
from datetime import date
from pathlib import Path

from publish import POSTS, PUBLIC_ANSWERS, parse, public_answer_card

FIRST_PUBLICATION = date(2026, 11, 24)


def build(posts, output):
    catalog = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {}
    current = 0
    for path in sorted(posts.glob("*.md")):
        post = parse(path)
        if post["time"].date() < FIRST_PUBLICATION:
            continue
        post["name"] = path.name
        card = public_answer_card(post)
        if card:
            key, entry = card
            catalog[key] = entry
            current += 1
    # Keep cards used in posts that are already on readers' phones.
    temporary = output.with_suffix(".tmp")
    temporary.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return current


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--posts", type=Path, default=POSTS)
    parser.add_argument("--output", type=Path, default=PUBLIC_ANSWERS)
    args = parser.parse_args()
    print("Открытых разборов в расписании:", build(args.posts, args.output))
