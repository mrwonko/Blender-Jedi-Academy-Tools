---
name: blender-tests
description: Run this repo's headless Blender test suite (tests/run_tests.py) via podman against one or more pinned Blender versions. Use before a commit/PR, or to check cross-version compatibility.
---

# Run the headless Blender test suite

A fixed script instead of an ad-hoc `podman run ... -v "$(pwd)":/repo:Z ...` invocation, so it can
be whitelisted in permission settings by exact path rather than needing a broader `podman run *`
rule (the `$(pwd)`-based mount is what made the ad-hoc version unsafe to whitelist as a fixed
pattern — every invocation embeds a dynamic shell substitution).

```
.claude/skills/blender-tests/run_blender_tests.sh <version> [<version> ...]
# e.g.
.claude/skills/blender-tests/run_blender_tests.sh 5.2
.claude/skills/blender-tests/run_blender_tests.sh 4.1 4.5 5.0 5.1 5.2
```

Pulls `docker.io/blenderkit/headless-blender:blender-<version>-stable` if not already present,
mounts the repo read-write at `/repo` inside the container, and runs
`blender --background --python-exit-code 1 --python /repo/tests/run_tests.py`. Exit 0 only if
every version's test run exits 0. Doesn't rely on the caller's `$(pwd)` or take a repo path — it
derives the repo root from its own on-disk location, so call it directly from any cwd.

Matches this repo's CI matrix (currently `4.1`/`5.2`, see `.github/workflows/ci.yml`) — use the
full `4.1 4.5 5.0 5.1 5.2` set for a broader local check before a version-support-affecting
change, matching what CLAUDE.md's "Known Blender version support" section says has been
spot-checked.
