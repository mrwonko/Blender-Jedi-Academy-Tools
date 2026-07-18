---
name: release
description: Cut a versioned release of this addon end-to-end -- decide the version bump, update the changelog, open the release PR, and tag the merged commit once it's ready. Use when the user asks to cut/push/ship a release.
---

# Cutting a release

Full process per `CLAUDE.md`'s "Releases" section, with the historically error-prone step (tagging
the right commit) backed by a validation script. Most steps are plain git/gh commands you already
know how to run — only Step 5 has a dedicated script, because it's the one step with a documented
history of mistakes (see PR #99: tagging `master`'s merge-commit HEAD instead of the actual
version-bump commit, since this repo merges PRs as merge commits).

## Step 1 — Decide whether a version bump is needed, and to what

Gather these facts directly (no script — cheap one-off reads):
- Most recent released version: latest `\subsection*{X.Y.Z}` heading in
  `jediacademy_plugins_doc.tex` (equivalently, the latest `vX.Y.Z` git tag: `git tag -l 'v*'`).
- Current `bl_info["version"]` in `__init__.py`.
- Bullets currently accumulated under the `\subsection*{next version}` placeholder heading.
- Commits/PRs merged since the last release tag (`git log <last-tag>..origin/master --oneline`).

While reading those bullets, check each one actually describes something that reached a real
user: a bug introduced and fixed before it ever merged to `master` (e.g. caught during the same
PR's development, or in review) was never in anything a user could have gotten, not even a
nightly build — remove that bullet rather than list it as a "fix". See `CLAUDE.md`'s changelog
convention.

**Important nuance**: per `CLAUDE.md`'s "bump immediately in the PR that necessitates it"
convention, `bl_info["version"]` may *already* have been bumped in some earlier PR, well before
this release-cutting PR — don't assume every release-cut PR bumps it itself.
- If `bl_info["version"]` already differs from the last released version: a bump already
  happened early. Sanity-check the magnitude against the accumulated changelog bullets (e.g. a
  breaking-change bullet demands major; if `bl_info` only got a minor bump, that's a mismatch to
  flag) — but don't bump it again if it already looks right.
- If `bl_info["version"]` still equals the last released version: decide the bump level yourself
  from the accumulated bullets, using `CLAUDE.md`'s two documented major-bump triggers (dropped
  Blender version support; a storage-format change that breaks forward-reading by older plugin
  versions) — major for either, otherwise minor/patch by ordinary judgment. Edit `__init__.py`'s
  `bl_info["version"]` as part of this same change if a bump is needed now.

## Step 2 — Rename the changelog heading

Edit `jediacademy_plugins_doc.tex`: change `\subsection*{next version}` to the real
`\subsection*{X.Y.Z}`. Don't touch older dated entries above it.

## Step 3 — Commit with the release notes as the message

Two non-obvious rules:
- **The commit message becomes the GitHub Release body verbatim** —
  `.github/workflows/ci.yml`'s `release` job runs `git log -1 --format=%B "$GITHUB_SHA"` on the
  tagged commit and uses that as the release notes. Write it as real, user-facing release notes,
  not a normal dev-facing commit message.
- **Do not** append the usual `Claude-Session`/`Co-Authored-By` trailer to this commit — it would
  end up in the public release notes.

Same never-reached-a-user check from Step 1 applies here too — don't carry a bullet for an
unshipped bug into the release-notes commit message just because it's still in the `.tex` file at
this point; catching it in Step 1 should have already removed it.

## Step 4 — Open the PR, wait for merge

Standard branch/PR flow. For "wait for merge": open the PR and stop there — only proceed to Step 5
once the user confirms it merged, or a fresh `gh pr view <n> --json state` shows `MERGED`. Don't
poll/auto-wait; this mirrors how every PR in this project actually gets merged (a human decides).

## Step 5 — Tag the correct commit

```
.claude/skills/release/tag_release.sh [-y|--yes] <version> <#pr-number|sha>
# e.g.
.claude/skills/release/tag_release.sh 2.0.0 '#106'
.claude/skills/release/tag_release.sh 2.0.0 a1b2c3d
.claude/skills/release/tag_release.sh -y 2.0.0 '#106'
```
(Quote the `#pr-number` form — unquoted `#` starts a shell comment.)

Running this via an agent's shell tool has no TTY, so the script's final confirmation prompt
(see below) can't be answered and the script exits with an error telling you to re-run with
`-y`/`--yes`. Pass `-y` to skip straight to tagging/pushing once all checks pass — get the
user's explicit go-ahead first, since this remains a real, hard-to-reverse publish action even
with the prompt skipped.

Resolves a `#`-prefixed PR number to that PR's branch tip via `gh` (a bare digit string is
*not* treated as a PR number, since a real commit SHA could in principle be all-decimal-digits —
`#` is required to disambiguate). Then, in order, refuses with a clear reason if any of these
fail:
1. The commit is reachable from `origin/master` (the same check the `release` CI job itself
   performs).
2. The commit is **not** a merge commit (has exactly one parent). A clean, non-conflicting
   "Merge pull request #N" merge has the exact same tree as its non-`master` parent, so checks
   3/4 below (which only inspect tree content) can't otherwise distinguish a merge commit from
   the real release commit sitting right under it — this is the actual PR #99 mistake tagging
   used to hit.
3. `bl_info["version"]` *at that commit* (not the working tree) equals the target version.
4. `jediacademy_plugins_doc.tex` *at that commit* has the real-version heading from Step 2, not
   just the `next version` placeholder.
5. The tag doesn't already exist, locally or on `origin`.

Deliberately **not** checked: whether `smoke-test`/`typecheck` will pass for the tagged commit.
If the `release` job's `needs` gate fails after tagging, GitHub's normal failure-notification
email is enough signal — pushing a small follow-up patch release to fix it is an acceptable
response, so this isn't worth pre-checking here.

Only if all five pass does it print the commit and prompt for confirmation before actually
tagging and pushing. **This script is deliberately not in the permission auto-allow list** —
unlike other project skills' scripts, creating and pushing a release tag is a real, hard-to-reverse
publish action (triggers the `release` job, publishes a public GitHub Release), so it should keep
prompting every time rather than being whitelisted. The validation logic itself is read-only and
safe; what's not safe to skip confirming is the tag+push at the end.
