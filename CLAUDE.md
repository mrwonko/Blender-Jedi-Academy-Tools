# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Blender add-on (not a standalone app) providing importers/exporters for Jedi Knight 2 / Jedi Academy
file formats — most importantly Ghoul 2 models (`.glm`) and animations (`.gla`), plus ASE, ROFF, MD3, and
Quake 3-style patch mesh (curved surface, `.map`) export. The GLM/GLA code is the core: it must roundtrip
losslessly (logically — see "Roundtripping" below), since its purpose is editing existing shipped
models/animations, not just one-way conversion.

The GLM/GLA import/export path is the actively-maintained, known-working core. It is unknown whether the
ASE, ROFF, MD3, and/or patch mesh im-/exporters still work — don't assume they're covered by the same
level of confidence, and treat their behavior as unverified unless you check.

There is currently no automated test suite — testing has been manual (load the add-on in Blender, import/export
files, compare). If asked to add tests, see "Testing" below for the intended direction.

## Commands

- `make` (or `make all`) — builds `build/jediacademy.zip` (the installable add-on package) and
  `build/jediacademy_plugins_doc.pdf` (compiled from `jediacademy_plugins_doc.tex` via `pdflatex`).
- `make build/jediacademy.zip` — package just the add-on `.py` files (see `PY_FILES` in `Makefile`) plus
  the readme into a zip installable via Blender's add-on preferences.
- CI (`.github/workflows/ci.yml`) runs `smoke-test` and `typecheck` on every PR, `vX.Y.Z` tag push, and
  on its daily `schedule`/manual `workflow_dispatch` — deliberately *not* on every push to `master`,
  since a PR already ran them before merge. On a `schedule` tick specifically, they're also skipped if
  there's nothing to do (see `check-nightly-needed` below) — a no-op nightly tick doesn't spin up the
  Blender matrix or pyright for nothing. Two more jobs depend on `smoke-test`/`typecheck`
  (`needs: [smoke-test, typecheck]`) and only run/publish if both passed (or were skipped as a no-op):
  `nightly` (force-updates the `nightly` prerelease tag/release with a freshly built manual and zip;
  only on the `schedule`/`workflow_dispatch` triggers, and on `schedule` only if `master` has new commits
  since the last nightly *attempt* — checked via the `check-nightly-needed` job, which always runs
  regardless of trigger, against a `nightly-attempted` tag that `nightly` moves as its first step
  regardless of whether the rest of the job succeeds, so a failure gets tried once and then left alone
  until master moves again rather than retried every night against the same broken commit; manual
  `workflow_dispatch` deliberately bypasses this check every time, as a way to force-retry a spurious
  failure on demand) and `release` (publishes a real GitHub Release for `vX.Y.Z` tag pushes — see
  "Releases" below).
- Formatting/linting: pycodestyle via `.pep8` (only rule disabled: E501 line length, to allow long
  `# pyright: ignore` comments). VS Code is configured (`.vscode/settings.json`) to use `autopep8` as the
  Python formatter and pyright type checking at `standard` mode. There's no separate CLI lint command
  currently wired up — run `pycodestyle` / `pyright` directly if checking manually.

### Known Blender version support

The add-on targets Blender as declared in `bl_info["blender"]` in `__init__.py`. Blender 5.2 is the latest
confirmed-working version (CI tests the 4.1/5.2 boundaries; 4.5/5.0/5.1 were spot-checked locally too).
Blender 5.0 introduced a breaking change to custom-property storage (`bpy.props`-registered properties
are no longer visible via dict-style `"key" in obj`/`obj.keys()` access) — this required reworking how
Ghoul 2 properties (`obj.g2_prop`) are stored and checked for existence; see the `PointerProperty`/
sentinel-custom-property pattern in `JAG2Panels.py` if touching that code. When diagnosing failures
reported against a specific Blender version, check that version against this before assuming a code bug.

### Releases

Versioned releases use plain SemVer (`bl_info["version"]` in `__init__.py`), decoupled from Blender
compatibility: `bl_info["blender"]` separately tracks the minimum supported Blender version, and which
version(s) a release was tested against is stated in the release notes / CI matrix, not encoded into the
version number itself. **Dropping support for a Blender version (raising the stated minimum) is a breaking
change and bumps the major version.** So is changing the on-disk custom-property storage format in a way
that makes files saved by a newer plugin version unreadable by older plugin versions — this doesn't
require dropping any Blender version, but breaks forward compatibility just the same.

**When a merged (or about-to-merge) change is known to require a version bump at the next release**
(most commonly a major bump from a breaking change like the above), bump `bl_info["version"]`
immediately as the first commit of the PR that necessitates it, rather than deferring it to the
dedicated release-cutting PR described below. `master` feeds the rolling `nightly` prerelease
continuously, so leaving the version number stale until the eventual release-cut PR would mean
nightlies built in the interim misreport their own compatibility.

The manual's changelog (`jediacademy_plugins_doc.tex`, "Changelog" section) tracks entries by version
rather than by date going forward. A PR with a user-facing change adds a bullet under a
`\subsection*{next version}` placeholder heading (create it if it doesn't exist yet) — internal-only
changes (CI, test infra, refactors, type annotations) are excluded, per the convention established in
PR #93. Cutting a release renames that placeholder heading to the real version, e.g.
`\subsection*{1.0.0}`; existing dated entries from before this convention are left as historical record,
not retroactively renamed.

To cut a release:
1. Open a PR that bumps `bl_info["version"]`, renames the changelog's `next version` placeholder to the
   real version number, and has a commit message written *as the release notes* — it becomes the GitHub
   Release body verbatim.
2. After that PR merges to `master`, tag `vX.Y.Z` and push the tag. **This repo merges PRs as merge
   commits, so `master`'s HEAD right after merging is a "Merge pull request #N..." commit, not the
   version-bump commit** — the `release` job (in `.github/workflows/ci.yml`) reads the tagged commit's
   message verbatim as the release notes, so tag the version-bump commit itself (its SHA is the PR
   branch's tip, e.g. from `gh pr view <N> --json commits`), not `master`'s literal HEAD. It just needs
   to be reachable from `master`, not be its tip — verified via `git log --graph` before tagging.
   That `release` job then builds the zip/manual and publishes the GitHub Release automatically, but only
   once `smoke-test`/`typecheck` pass for that tagged commit (`needs: [smoke-test, typecheck]`), and only
   for tags reachable from `master` (a merge-base check guards against a stray tag on some other commit).
3. The rolling `nightly` prerelease (the `nightly` job in `.github/workflows/ci.yml`) is unaffected and
   keeps publishing daily (`schedule`) or on manual `workflow_dispatch`, gated the same way, alongside
   versioned releases.

### Testing (planned direction)

When implementing test infrastructure for this repo, the intended approach is:
- Use version-pinned Blender Docker images to run the add-on headlessly (`blender --background --python ...`)
  against each supported Blender version, so breakage from Blender API changes is caught per-version rather
  than discovered by users.
- Cover both directions: exporting from prepared `.blend` files, and full import→export roundtrips.
- **Don't reimplement file parsing to check results.** The `loadFromFile`/`saveToFile` binary (de)serialization
  in `JAG2GLM.py`/`JAG2GLA.py` has seen extensive practical use and can be assumed correct — reuse it. To check
  an export, load the produced file back into the in-memory model (`GLM`/`GLA` objects) with the existing
  `loadFromFile` and compare *that* structure/data against an expected in-memory model (or against the model
  loaded from a known-good reference file), rather than diffing raw bytes or re-parsing the format by hand.
- Comparisons must be logical, not byte-for-byte: see "Roundtripping" below for why, and for the one exception
  (bone order) that does need to be pinned down explicitly in test fixtures via the reference-skeleton export
  option.
- Releases are now versioned — see "Releases" above rather than treating this as still-planned.

### Roundtripping

"Lossless roundtrip" means logically lossless, not a byte-identical file. Elements such as surfaces may come
back out in a different order than they went in — that's expected and not a bug. (LODs are the exception:
their order is meaningful and fixed — LOD 0 is always the most detailed level, with each subsequent LOD
reduced further — so LOD order is not expected to shuffle.) When writing roundtrip tests, compare the
loaded-back in-memory model's data (bone transforms, vertex weights, surface hierarchy, etc.), not raw file
bytes or surface order.

**Bone order in `.gla` is the one place order genuinely matters**: `.glm` files reference bones by index
into the `.gla`'s bone list, so if a re-exported `.gla`'s bone order doesn't match the original, previously-valid
`.glm` files (and any other `.gla` meant to share indices, e.g. other animations for the same skeleton) would
silently reference the wrong bones. GLA export has a "reference skeleton" option for this: point it at an
existing `.gla` and the exporter mirrors that file's bone order. Roundtrip tests exporting a `.gla` should
generally use this option (pointing at the original file) so bone order is pinned rather than left to
incidental Blender iteration order — but tests may also legitimately exercise `.gla` export *without* a
reference skeleton, in which case bone order is allowed to differ from the original and comparisons must
account for that (e.g. compare bones by name, not by index).

`.gla` files themselves store a flat sequence of animation frames (poses), with no notion of named
sequences — that metadata (name, start frame, frame count, looping, playback speed) lives in `animation.cfg`
instead.

## Architecture

### Module reloading

Every module starts with a `reload_modules(...)` call from `mod_reload.py` before its real imports. This
makes Blender's F8 "Reload Scripts" pick up changes to internal modules during development, which Python's
normal import caching would otherwise prevent. When adding a new internal module or new cross-module
imports, register them in the appropriate `reload_modules` call in the importing module — otherwise edits
to that module won't be picked up until Blender is restarted.

### Layering

The codebase is layered import format → in-memory scene model → Blender operators/UI:

1. **Binary format layer** (`JAG2GLM.py`, `JAG2GLA.py`) — one class per on-disk structure (e.g. `MdxmHeader`,
   `MdxmSurface`, `MdxaBone`, `MdxaAnimation`), each with symmetric `loadFromFile`/`saveToFile` and
   `loadFromBlender`/`saveToBlender` methods. This is where the file format's byte layout and the Blender
   scene layout both live, side by side per-structure — read the matching pair of methods together when
   tracing how a field round-trips.
2. **Scene orchestration** (`JAG2Scene.py`) — the `Scene` class ties a `GLM` and a `GLA` together (a model
   needs its skeleton), handling the file lookup and load/save sequencing operators call into
   (`loadFromGLM`/`loadFromGLA`/`loadModelFromBlender`/`loadSkeletonFromBlender` and their `saveTo*`
   counterparts). `*default` is a special sentinel GLA path meaning "no skeleton file, synthesize a
   1-bone default skeleton" (used for weapons/static props).
3. **Blender integration** (`JAG2Operators.py`, `JAG2Panels.py`, `__init__.py`) — `bpy.types.Operator`
   subclasses (`GLMImport`, `GLAImport`, `GLMExport`, `GLAExport`, ...) expose the file dialogs and options,
   delegate to `Scene`, and are registered/added to Blender's import/export menus in `__init__.py`'s
   `register()`/`unregister()`. `JAG2Panels.py` adds the custom Ghoul 2 properties UI (name/tag/off flags)
   to the Object properties tab.

Supporting modules: `JAG2Constants.py` (shared enums, e.g. `SkeletonFixes`), `JAG2Math.py` (coordinate/matrix
conversions between Blender's and Ghoul 2's conventions — e.g. `GLABoneRotToBlender`/`BlenderBoneRotToGLA`),
`JAFilesystem.py` (path helpers resolving GameData-relative paths), `JAMaterialmanager.py` (texture/skin
resolution on import), `casts.py` (typed helper casts working around `bpy`'s loose typing for pyright),
`error_types.py` (the `(bool, ErrorMessage)` / `Optional[T], ErrorMessage` result convention used throughout
instead of exceptions for expected failure paths — see `NoError`/`ErrorMessage`).

ASE (`JAAseImport.py`/`JAAseExport.py`), ROFF (`JARoffImport.py`/`JARoffExport.py`), MD3
(`JAMd3Export.py`/`JAMd3Encode.py`), and the animation.cfg patch exporter (`JAPatchExport.py`) are separate,
simpler formats that don't go through `JAG2Scene`/`Scene` — they're standalone import/export pairs.

### Error handling convention

Functions that can fail return `Tuple[bool, ErrorMessage]` (or `Tuple[Optional[T], ErrorMessage]`) rather
than raising — check `success`/`None` and propagate the message upward to the operator, which surfaces it
in Blender's UI. Exceptions are reserved for actual bugs, not expected failure conditions (invalid file,
missing skeleton, etc.). Follow this convention for new code in the GLM/GLA/Scene layers rather than
introducing exception-based control flow.

### Ghoul 2 format constraints worth knowing when touching import/export code

These are real format limitations the exporter must enforce/handle (see `README.md` for the full list):
every vertex must be weighted; max 32 bones referenced per surface; max 4 bone weights per vertex; names
truncate silently at 64 characters; all LODs must share one object hierarchy (LOD 0's hierarchy wins);
bones must not be scaled and must not move >512 units from their parent/base pose; Jedi Academy additionally
caps surfaces at 1000 vertices. Required Blender-side naming: `skeleton_root` (armature), `model_root_<LOD>`
(LOD roots, starting at 0), `scene_root` (parent of all `model_root_*`, used as model origin).
