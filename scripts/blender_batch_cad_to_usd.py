import os
import re
from pathlib import Path
import time
import subprocess

def find_files(root_dir: str, pattern: str, max_depth: int, ignore_case = False):
    """
    Recursively search for files under `root_dir` up to `max_depth` levels deep,
    returning full paths for files whose names match the given regex `pattern`.

    Args:
        root_dir (str): The root directory to start searching from.
        pattern (str): A regular expression to match filenames (not paths).
        max_depth (int): Maximum depth to search (0 means only the root).

    Returns:
        list[str]: Full paths to matching files.
    """
    root_path = Path(root_dir).resolve()
    if ignore_case:
        regex = re.compile(pattern, re.IGNORECASE)
    else:
        regex = re.compile(pattern)
    matches = []

    # Walk manually with depth control
    def _walk(dir_path: Path, depth: int):
        if depth > max_depth:
            return
        for entry in os.scandir(dir_path):
            if entry.is_file() and regex.search(entry.name):
                matches.append(str(Path(entry.path).resolve()))
            elif entry.is_dir():
                _walk(Path(entry.path), depth + 1)

    _walk(root_path, 0)
    return matches

def run_blender(mesh_folder):
    """Run Blender in background mode on one folder."""
    cmd = [
        BLENDER_PATH,
        "--background",
        "--python", CONVERSION_SCRIPT,
        "--", mesh_folder
    ]
    print(f"\n🚀 Running Blender on {mesh_folder}")
    start = time.time()
    result = subprocess.run(cmd)
    elapsed = time.time() - start
    success = (result.returncode == 0)
    if success:
        print(f"✅ Completed in {elapsed:.2f} seconds")
    else:
        print(f"❌ Failed after {elapsed:.2f} seconds (exit code {result.returncode})")
    return elapsed, success


# Path to blender executable
# BLENDER_PATH = "/home/csrobot/software/blender-4.3.2-linux-x64/blender"
BLENDER_PATH = "blender"
# Path to the blender python script we already wrote
CONVERSION_SCRIPT = "/home/csrobot/moad_cui/scripts/blender_convert_cad_to_usd.py"
if not os.path.exists(CONVERSION_SCRIPT):
    print(f"ERROR: Conversion script file not found, set it at the top of this script.\n Current: {CONVERSION_SCRIPT}")
    exit(1)

# == ASSEMBLE LIST OF CAD FILE PATHS ==
# Set root directory
search_root = "/home/csrobot/Omniverse/Models/ATB1_download"
max_search_depth = 5
search_pattern =  r"\.(stl)$"
# Search for '.stl' files
file_list = find_files(search_root,search_pattern,max_search_depth)
file_list = sorted(file_list)

# Show matches, pause before continuing 
print(f"Found {len(file_list)} matches:")
for f in file_list: print(f" > {f}")
input("Continue?:")

# For each stl file, run blender conversion
for cad_file in file_list:
    run_blender(cad_file)