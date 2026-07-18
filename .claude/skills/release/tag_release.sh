#!/usr/bin/env bash
# Validates a release commit and, only if every check passes, tags and pushes it.
#
# Usage: tag_release.sh [-y|--yes] <version> <#pr-number|sha>
#   -y, --yes      skip the interactive confirmation prompt and push immediately once all
#                   checks pass -- needed when running non-interactively (e.g. via an agent's
#                   shell tool, which has no TTY for `read` to prompt on). All the same checks
#                   still run first; this only removes the final human confirmation step, so
#                   only pass it once you've reviewed the printed commit/message yourself, or
#                   asked whoever you're acting on behalf of to confirm first.
#   version        e.g. 2.0.0 (no leading "v")
#   #pr-number     a leading "#" resolves to that PR's branch tip via `gh` (e.g. "#106")
#   sha             anything else is treated as a literal commit SHA -- a raw all-digit string
#                   is NOT treated as a PR number, since a real commit SHA could (in principle)
#                   consist entirely of decimal digits; "#" is required to mean "PR number".
#
# Repo root is derived from this script's own location, not the caller's cwd -- same reasoning
# as the check-syntax/blender-tests skills' scripts.
set -euo pipefail

ASSUME_YES=0
ARGS=()
for arg in "$@"; do
  case "$arg" in
    -y|--yes) ASSUME_YES=1 ;;
    *) ARGS+=("$arg") ;;
  esac
done

if [ "${#ARGS[@]}" -ne 2 ]; then
  echo "Usage: $(basename "$0") [-y|--yes] <version> <#pr-number|sha>   e.g. $(basename "$0") 2.0.0 '#106'" >&2
  exit 2
fi

VERSION="${ARGS[0]}"
REF="${ARGS[1]}"

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
  # --json headRefOid, not --json commits --jq '.commits[-1].oid': commits is a list that
  # could in principle be capped for a PR with a huge commit count, whereas headRefOid names
  # the tip directly. Guarded explicitly (not a bare `SHA=$(...)`) so a resolution failure
  # (bad PR number, no network) prints our own message instead of a raw gh/GraphQL error.
  if ! GH_OUTPUT="$(gh pr view "$PR_NUM" --json headRefOid --jq '.headRefOid' 2>&1)"; then
    echo "ERROR: couldn't resolve PR #$PR_NUM to a commit SHA: $GH_OUTPUT" >&2
    exit 1
  fi
  SHA="$GH_OUTPUT"
  if [ -z "$SHA" ]; then
    echo "ERROR: couldn't resolve PR #$PR_NUM to a commit SHA (empty result)" >&2
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

# 1. Commit must exist and be reachable from origin/master. This mirrors ci.yml's release job's
#    own "Verify tag is on master" step (kept in sync by hand -- both are one `git merge-base`
#    line, not worth extracting a shared script for); catching it here means a bad tag never
#    reaches the point of confusing CI.
git cat-file -e "${SHA}^{commit}" 2>/dev/null || fail "commit $SHA does not exist"
git merge-base --is-ancestor "$SHA" origin/master \
  || fail "commit $SHA is not reachable from origin/master"

# 1b. Must not be a merge commit. A clean, non-conflicting "Merge pull request #N" merge has
#     the exact same tree as its non-master parent, so checks 2/3 below (which only inspect
#     tree content) can't otherwise tell a merge commit apart from the real release commit
#     sitting right under it -- the actual PR #99 mistake this script exists to prevent.
# `grep -c` exits nonzero when it finds zero matches (a 0-parent root commit, unrealistic as an
# actual release target but still worth not crashing on) -- `|| true` neutralizes that under
# `set -o pipefail`, same reasoning as the bl_info check above.
PARENT_COUNT="$(git cat-file -p "$SHA" | grep -c '^parent ' || true)"
if [ "$PARENT_COUNT" -gt 1 ]; then
  fail "commit $SHA has $PARENT_COUNT parents (a merge commit) -- tag the actual release commit (e.g. the PR branch tip), not a merge commit sitting on top of it"
fi

# 2. bl_info["version"] AT THAT COMMIT (not the working tree) must equal the target version.
#    `|| true` on the pipeline plus an explicit empty-string check, rather than a bare
#    assignment: under `set -o pipefail`, a no-match here (grep finds nothing) would otherwise
#    abort the whole script silently, before ever reaching the friendly `fail` message below.
BL_INFO_VERSION="$(git show "$SHA:__init__.py" 2>/dev/null \
  | grep -oP '"version":\s*\(\K[0-9]+,\s*[0-9]+,\s*[0-9]+' \
  | tr -d ' ' | tr ',' '.' || true)"
if [ -z "$BL_INFO_VERSION" ]; then
  fail "couldn't find bl_info[\"version\"] in __init__.py at $SHA (wrong format, or file missing at that commit?)"
fi
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
# --exit-code: 0 = tag found, 2 = no matching ref (genuinely doesn't exist), anything else is a
# real failure (network/auth). Checked explicitly rather than piping into `grep -q .`, which
# can't tell "found nothing" apart from "ls-remote itself failed and printed nothing" -- the
# latter would otherwise silently pass this check instead of failing loudly.
set +e
git ls-remote --exit-code --tags origin "refs/tags/v${VERSION}" >/dev/null 2>&1
REMOTE_TAG_STATUS=$?
set -e
if [ "$REMOTE_TAG_STATUS" -eq 0 ]; then
  fail "tag v${VERSION} already exists on origin"
elif [ "$REMOTE_TAG_STATUS" -ne 2 ]; then
  fail "couldn't check whether tag v${VERSION} exists on origin (git ls-remote exited $REMOTE_TAG_STATUS -- network/auth issue?)"
fi

echo "READY: $SHA passes all checks for v${VERSION}."
echo
git log -1 --format='commit %H%nauthor %an%n%n%B' "$SHA"
echo
if [ "$ASSUME_YES" -eq 1 ]; then
  echo "-y/--yes given, skipping confirmation prompt."
else
  # `read` fails (nonzero) on EOF -- e.g. no interactive terminal attached, which is the normal
  # case when this script is run via an agent's non-interactive shell tool rather than directly
  # in a terminal. Guarded explicitly so that case gets its own clear message (pointing at -y)
  # instead of silently exiting with no output at all (indistinguishable from a real check
  # failing above).
  if ! read -r -p "Create and push tag v${VERSION} at this commit? [y/N] " confirm; then
    echo "ERROR: couldn't read a confirmation answer (no interactive terminal attached?). Re-run with -y/--yes to skip the prompt, or run this script directly in an interactive shell to confirm manually." >&2
    exit 1
  fi
  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted, no tag created."
    exit 1
  fi
fi

git tag -a "v${VERSION}" "$SHA" -m "v${VERSION}"
git push origin "v${VERSION}"
echo "Pushed tag v${VERSION}. The release job in .github/workflows/ci.yml will pick it up once smoke-test/typecheck pass."
