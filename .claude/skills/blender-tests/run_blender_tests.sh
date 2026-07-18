#!/usr/bin/env bash
# Runs tests/run_tests.py headlessly in one or more versions of Blender via podman.
# Usage: run_blender_tests.sh <version> [<version> ...]   e.g. run_blender_tests.sh 4.1 5.2
#
# Repo root is derived from this script's own location, not the caller's cwd, so the
# invocation never needs a $(pwd)-style substitution at the call site -- that's what made
# the equivalent ad-hoc commands unsafe to whitelist as a fixed pattern.
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $(basename "$0") <version> [<version> ...]   e.g. $(basename "$0") 4.1 5.2" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

status=0
for version in "$@"; do
  echo "=== Blender $version ==="
  if ! podman run --rm \
    --entrypoint /home/headless/blender/blender \
    -v "$REPO_ROOT:/repo:Z" \
    "docker.io/blenderkit/headless-blender:blender-${version}-stable" \
    --background --python-exit-code 1 --python /repo/tests/run_tests.py; then
    status=1
  fi
done
exit "$status"
