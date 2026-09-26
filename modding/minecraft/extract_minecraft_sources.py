import os
import re
import subprocess
import shutil
from pathlib import Path

# --- Strict mode equivalents --------------------------------------------------

def fail(message):
    raise RuntimeError(message)

# --- Resolve project root and gradle.properties -------------------------------

project_root = Path.cwd()
properties_path = project_root / "gradle.properties"

if not properties_path.exists():
    fail("gradle.properties was not found in the current directory. Run this script from the project root.")

# --- Extract minecraft_version -------------------------------------------------

minecraft_version = None
pattern = re.compile(r'^\s*minecraft_version\s*=\s*(.+?)\s*$')

with properties_path.open("r", encoding="utf-8") as f:
    for line in f:
        match = pattern.match(line)
        if match:
            minecraft_version = match.group(1).strip()
            break

if not minecraft_version:
    fail("minecraft_version was not found in gradle.properties.")

# --- Validate gradlew.bat -----------------------------------------------------

gradlew = project_root / "gradlew.bat"
if not gradlew.exists():
    fail("gradlew.bat was not found in the current directory. Run this script from the project root.")

# --- Run genSources -----------------------------------------------------------

print(f"Generating Minecraft sources for {minecraft_version}...")
result = subprocess.run([str(gradlew), "genSources"], shell=True)

if result.returncode != 0:
    fail(f"genSources failed with exit code {result.returncode}.")

# --- Locate Loom Minecraft cache ---------------------------------------------

minecraft_maven_root = project_root / ".gradle" / "loom-cache" / "minecraftMaven" / "net" / "minecraft"

if not minecraft_maven_root.exists():
    fail(f"Loom Minecraft cache was not found at {minecraft_maven_root}.")

# --- Find source jars ---------------------------------------------------------

source_jars = sorted(
    p for p in minecraft_maven_root.rglob(f"*{minecraft_version}*-sources.jar")
    if re.match(r'^minecraft-.+-sources\.jar$', p.name)
)

if not source_jars:
    fail(f"No Minecraft source jars for {minecraft_version} were found under {minecraft_maven_root}.")

# --- Prepare destination -------------------------------------------------------

destination_root = Path(r"C:\minecraft-assets") / minecraft_version
source_destination = destination_root / "source"
source_destination.mkdir(parents=True, exist_ok=True)

print(f"Extracting Minecraft sources into {source_destination}...")

# --- Extract each source jar --------------------------------------------------

for jar_path in source_jars:
    print(f"Extracting {jar_path.name}")
    try:
        subprocess.run(["jar", "xf", str(jar_path)], cwd=str(source_destination), check=True)
    except subprocess.CalledProcessError as e:
        fail(f"jar failed with exit code {e.returncode} while extracting {jar_path}")

print(f"Done. Extracted {len(source_jars)} Minecraft source jar(s) to {source_destination}.")
