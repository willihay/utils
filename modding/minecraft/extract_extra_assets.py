import json
import os
import shutil
import argparse

# ------------------------------------------------------------
# Helper: find first JSON index file in the indexes directory
# ------------------------------------------------------------
def find_default_index(indexes_dir):
    for name in os.listdir(indexes_dir):
        if name.endswith(".json"):
            return os.path.join(indexes_dir, name)
    raise FileNotFoundError("No index JSON files found in " + indexes_dir)


# ------------------------------------------------------------
# Main extraction logic
# ------------------------------------------------------------
def extract_assets(index_file, objects_dir, output_dir, dry_run=False, sounds_only=False, include_lang=False):
    print(f"Using index file: {index_file}")
    print(f"Output directory: {output_dir}")
    print(f"Dry run mode: {'ON' if dry_run else 'OFF'}")
    print(f"Extracting only sounds (.ogg): {'YES' if sounds_only else 'NO'}")
    print(f"Including lang files: {'YES' if include_lang else 'NO'}")

    # Load index JSON
    with open(index_file, "r") as f:
        index = json.load(f)

    objects = index["objects"]

    extracted_count = 0

    for logical_path, info in objects.items():

        # Skip lang files unless override is enabled
        if logical_path.startswith("minecraft/lang/") and not include_lang:
            continue

        # If sounds-only mode is enabled, skip non-ogg files
        if sounds_only and not logical_path.endswith(".ogg"):
            continue

        hash_val = info["hash"]
        subdir = hash_val[:2]
        object_path = os.path.join(objects_dir, subdir, hash_val)

        output_path = os.path.join(output_dir, logical_path)

        if dry_run:
            print(f"[DRY RUN] Would extract: {logical_path}")
        else:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            shutil.copyfile(object_path, output_path)

        extracted_count += 1

    print(f"Done. {'Would have extracted' if dry_run else 'Extracted'} {extracted_count} files.")


# ------------------------------------------------------------
# CLI argument parsing
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Extract extra Minecraft assets from objects folder using index file.")
    parser.add_argument("-i", "--index", help="Override index file name (e.g., 1.21.11.json)")
    parser.add_argument("-d", "--dry-run", action="store_true", help="Preview files without extracting")
    parser.add_argument("-l", "--include-lang", action="store_true", help="Include lang files in extraction")
    parser.add_argument("-s", "--sounds-only", action="store_true", help="Extract only .ogg sound files")
    parser.add_argument("-o", "--output", help="Specify output directory")
    args = parser.parse_args()

    # Resolve Minecraft directory (Windows-safe)
    minecraft_dir = os.path.join(os.environ["APPDATA"], ".minecraft")
    indexes_dir = os.path.join(minecraft_dir, "assets", "indexes")
    objects_dir = os.path.join(minecraft_dir, "assets", "objects")

    # Determine index file
    if args.index:
        index_file = os.path.join(indexes_dir, args.index)
        if not os.path.exists(index_file):
            raise FileNotFoundError(f"Index file not found: {index_file}")
    else:
        index_file = find_default_index(indexes_dir)

    # Determine output directory
    if args.output:
        output_dir = os.path.expanduser(args.output)
    else:
        output_dir = os.path.expanduser("~/source/minecraft/extra-assets")

    extract_assets(
        index_file,
        objects_dir,
        output_dir,
        dry_run=args.dry_run,
        sounds_only=args.sounds_only,
        include_lang=args.include_lang
    )


if __name__ == "__main__":
    main()
