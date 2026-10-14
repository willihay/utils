#!/usr/bin/env python3
import argparse
import os
import gzip
import zipfile
import io
import sys
import re
import string

PRINTABLE = set(bytes(string.printable, "ascii"))

def is_printable(data: bytes) -> bool:
    """Return True if all bytes are printable text (tabs/newlines allowed)."""
    for b in data:
        if b not in PRINTABLE and b not in (9, 10, 13):
            return False
    return True


def search_in_text(text: str, pattern: str, ignore_case: bool) -> bool:
    flags = re.IGNORECASE if ignore_case else 0
    return re.search(pattern, text, flags) is not None


def search_regular_file(path: str, pattern: str, ignore_case: bool):
    try:
        with open(path, "rb") as f:
            data = f.read()
        if not is_printable(data):
            return False
        text = data.decode("utf-8", errors="ignore")
        return search_in_text(text, pattern, ignore_case)
    except Exception:
        return False


def search_gzip(path: str, pattern: str, ignore_case: bool):
    try:
        with gzip.open(path, "rb") as f:
            data = f.read()
        if not is_printable(data):
            return False
        text = data.decode("utf-8", errors="ignore")
        return search_in_text(text, pattern, ignore_case)
    except Exception:
        return False


def search_zip(path: str, pattern: str, ignore_case: bool):
    try:
        with zipfile.ZipFile(path, "r") as z:
            for name in z.namelist():
                try:
                    data = z.read(name)
                    if not is_printable(data):
                        continue
                    text = data.decode("utf-8", errors="ignore")
                    if search_in_text(text, pattern, ignore_case):
                        return True
                except Exception:
                    continue
    except Exception:
        return False
    return False


def search_file(path: str, pattern: str, ignore_case: bool):
    ext = os.path.splitext(path)[1].lower()

    if ext == ".gz":
        return search_gzip(path, pattern, ignore_case)
    elif ext == ".zip":
        return search_zip(path, pattern, ignore_case)
    else:
        return search_regular_file(path, pattern, ignore_case)


def walk_files(base_path: str, recurse: bool):
    if recurse:
        for root, dirs, files in os.walk(base_path):
            for f in files:
                yield os.path.join(root, f)
    else:
        for f in os.listdir(base_path):
            full = os.path.join(base_path, f)
            if os.path.isfile(full):
                yield full


def main():
    parser = argparse.ArgumentParser(
        description="Search text inside files, including .gz and .zip archives."
    )
    parser.add_argument(
        "pattern",
        help="Search pattern (regular expression)"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Optional directory to search (default: current directory)"
    )
    parser.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        help="Ignore case when searching"
    )
    parser.add_argument(
        "-r",
        "--recurse",
        action="store_true",
        help="Search subdirectories recursively"
    )

    args = parser.parse_args()

    base_path = args.path
    pattern = args.pattern

    if not os.path.isdir(base_path):
        print(f"Error: '{base_path}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    for path in walk_files(base_path, args.recurse):
        if search_file(path, pattern, args.ignore_case):
            print(path)


if __name__ == "__main__":
    main()
