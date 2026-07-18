#!/usr/bin/env bash
# Validates a release commit and, only if every check passes, tags and pushes it.
#
# Usage: tag_release.sh <version> <#pr-number|sha>
#   version        e.g. 2.0.0 (no leading "v")
#   #pr-number     a leading "#" resolves to that PR's branch tip via `gh` (e.g. "#106")
#   sha             anything else is treated as a literal commit SHA -- a raw all-digit string
#                   is NOT treated as a PR number, since a real commit SHA could (in principle)
#                   consist entirely of decimal digits; "#" is required to mean "PR number".
#
# Repo root is derived from this script's own location, not the caller's cwd -- same reasoning
# as the check-syntax/blender-tests skills' scripts.
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $(basename "$0") <version> <#pr-number|sha>   e.g. $(basename "$0") 2.0.0 '#106'" >&2
  exit 2
fi

VERSION="$1"
REF="$2"

if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "ERROR: version must look like X.Y.Z (no leading 'v'), got: $VERSION" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

if [[ "$REF" =~ ^#([0-9]+)$ ]]; then
  PR_NUM="${BASH_REMATCH[1]}"
  echo "Resolving PR #$PR_NUM to its branch tip commit..."
  SHA="$(gh pr view "$PR_NUM" --json commits --jq '.commits[-1].oid')"
  if [ -z "$SHA" ]; then
    echo "ERROR: couldn't resolve PR #$PR_NUM to a commit SHA" >&2
    exit 1
  fi
  echo "PR #$PR_NUM tip: $SHA"
else
  SHA="$REF"
fi

git fetch origin --quiet

fail() {
  echo "NOT READY: $1" >&2
  exit 1
}

# 1. Commit must exist and be reachable from origin/master -- the same check ci.yml's release
#    job performs; catching it here means a bad tag never reaches the point of confusing CI.
git cat-file -e "${SHA}^{commit}" 2>/dev/null || fail "commit $SHA does not exist"
git merge-base --is-ancestor "$SHA" origin/master \
  || fail "commit $SHA is not reachable from origin/master"

# 2. bl_info["version"] AT THAT COMMIT (not the working tree) must equal the target version.
BL_INFO_VERSION="$(git show "$SHA:__init__.py" \
  | grep -oP '"version":\s*\(\K[0-9]+,\s*[0-9]+,\s*[0-9]+' \
  | tr -d ' ' | tr ',' '.')"
if [ "$BL_INFO_VERSION" != "$VERSION" ]; then
  fail "bl_info[\"version\"] at $SHA is ($BL_INFO_VERSION), expected ($VERSION)"
fi

# 3. The changelog must have a heading for this real version at that commit, i.e. the
#    \subsection*{next version} placeholder was already renamed there.
if ! git show "$SHA:jediacademy_plugins_doc.tex" \
    | grep -qF "\\subsection*{${VERSION}}"; then
  fail "jediacademy_plugins_doc.tex at $SHA has no \\subsection*{${VERSION}} heading"
fi

# 4. Tag must not already exist, locally or on origin.
if git rev-parse -q --verify "refs/tags/v${VERSION}" >/dev/null; then
  fail "tag v${VERSION} already exists locally"
fi
if git ls-remote --tags origin "refs/tags/v${VERSION}" | grep -q .; then
  fail "tag v${VERSION} already exists on origin"
fi

echo "READY: $SHA passes all checks for v${VERSION}."
echo
git log -1 --format='commit %H%nauthor %an%n%n%B' "$SHA"
echo
read -r -p "Create and push tag v${VERSION} at this commit? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted, no tag created."
  exit 1
fi

git tag -a "v${VERSION}" "$SHA" -m "v${VERSION}"
git push origin "v${VERSION}"
echo "Pushed tag v${VERSION}. The release job in .github/workflows/ci.yml will pick it up once smoke-test/typecheck pass."
