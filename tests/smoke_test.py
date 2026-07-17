import importlib.util
import os
import sys

print("[smoke_test] Starting Jedi Academy Tools CI smoke test...")

# The repo's own folder name (e.g. "Blender-Jedi-Academy-Tools") isn't a valid Python
# identifier and won't match wherever it happens to be checked out, so register it as
# the "jediacademy" package explicitly instead of relying on the on-disk directory name.
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "jediacademy", os.path.join(repo_root, "__init__.py"),
    submodule_search_locations=[repo_root],
)
jediacademy = importlib.util.module_from_spec(spec)
sys.modules["jediacademy"] = jediacademy
spec.loader.exec_module(jediacademy)
print(f"[smoke_test] Imported jediacademy OK: {jediacademy.bl_info['name']}")

# Toggle to False to verify CI failure reporting, then flip back before merging.
SHOULD_PASS = False

if SHOULD_PASS:
    print("[smoke_test] PASS: pipeline is wired up correctly.")
else:
    print("[smoke_test] FAIL: deliberately raising to verify CI failure reporting.")
    raise RuntimeError("[smoke_test] Deliberate failure for pipeline verification")

print("[smoke_test] Done.")
