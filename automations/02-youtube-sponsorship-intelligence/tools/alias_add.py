"""CLI: fold a brand name into the alias map.

Usage:
  python tools/alias_add.py "<raw name>" <canonical> [display] [--file brand_aliases.seed.json]

Example (after a report flags 'Magic Spoon' as unmatched):
  python tools/alias_add.py "Magic Spoon" magicspoon "MagicSpoon"
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline import alias_admin  # noqa: E402


def main(argv=None):
    p = argparse.ArgumentParser(description="Add a brand alias")
    p.add_argument("raw_name")
    p.add_argument("canonical")
    p.add_argument("display", nargs="?", default=None)
    p.add_argument("--file", default=os.path.join(os.path.dirname(__file__), "..", "brand_aliases.seed.json"))
    a = p.parse_args(argv)

    with open(a.file, encoding="utf-8") as fh:
        aliases = json.load(fh)
    updated = alias_admin.add_alias(aliases, a.raw_name, a.canonical, a.display)
    with open(a.file, "w", encoding="utf-8") as fh:
        json.dump(updated, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("Added '%s' -> %s (%d aliases total)" % (a.raw_name, a.canonical, len(updated)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
