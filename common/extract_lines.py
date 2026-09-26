import sys
import os

def extract_lines(log_path, search):
    # Resolve relative path
    full_path = os.path.abspath(log_path)

    with open(full_path, "r", encoding="utf-8") as f:
        for line in f:
            if search in line:
                print(line.rstrip())

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_lines.py <log_path> <search_string>")
        sys.exit(1)

    log_path = sys.argv[1]
    search = sys.argv[2]

    extract_lines(log_path, search)
