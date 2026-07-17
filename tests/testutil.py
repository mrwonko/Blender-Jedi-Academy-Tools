import importlib.util
import sys
import os
from types import ModuleType
from typing import TYPE_CHECKING, Callable, List, Optional, Set, Tuple, cast

if TYPE_CHECKING:
    import JAG2GLA
    import JAG2GLM
    import JAG2Math
    import mathutils


def import_addon() -> ModuleType:
    """Import the repo as the 'jediacademy' package regardless of its on-disk directory name."""
    if "jediacademy" in sys.modules:
        return sys.modules["jediacademy"]
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location(
        "jediacademy", os.path.join(repo_root, "__init__.py"),
        submodule_search_locations=[repo_root],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["jediacademy"] = module
    spec.loader.exec_module(module)
    return module


def reset_scene() -> None:
    """Clear all Blender state between test cases so one case can't leak objects/data into the next."""
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)


class TestRunner:
    """Runs each case, logs pass/fail immediately, defers raising until every case has run."""

    def __init__(self) -> None:
        self.results: List[Tuple[str, Optional[Exception]]] = []

    def run(self, name: str, fn: Callable[[], None]) -> None:
        print(f"[test] Running {name}...")
        try:
            fn()
        except Exception as e:
            print(f"[test] {name}: FAIL - {e}")
            self.results.append((name, e))
        else:
            print(f"[test] {name}: PASS")
            self.results.append((name, None))

    def report(self) -> None:
        print("[test] === Summary ===")
        failed = []
        for name, err in self.results:
            print(f"[test]   {name}: {'FAIL' if err else 'PASS'}")
            if err is not None:
                failed.append(name)
        if failed:
            raise RuntimeError(f"{len(failed)}/{len(self.results)} test case(s) failed: {', '.join(failed)}")


def check(mismatches: List[str]) -> None:
    """A case's assertion helper: turn a list of mismatch strings into an exception if non-empty."""
    if mismatches:
        raise AssertionError(f"{len(mismatches)} mismatch(es):\n" + "\n".join(f"  - {m}" for m in mismatches))


def _decode(bs: bytes) -> str:
    return import_addon().JAStringhelper.decode(bs)


def _surface_name(surface_data_collection: "JAG2GLM.MdxmSurfaceDataCollection", index: int) -> str:
    return _decode(surface_data_collection.surfaces[index].name)


def compare_glm(actual: "JAG2GLM.GLM", expected: "JAG2GLM.GLM") -> List[str]:
    """Structural comparison of two JAG2GLM.GLM objects. Returns a list of mismatch descriptions."""
    mismatches = []

    actual_coll = actual.surfaceDataCollection
    expected_coll = expected.surfaceDataCollection

    actual_by_name = {_surface_name(actual_coll, s.index): s for s in actual_coll.surfaces}
    expected_by_name = {_surface_name(expected_coll, s.index): s for s in expected_coll.surfaces}

    actual_names = set(actual_by_name)
    expected_names = set(expected_by_name)
    if actual_names != expected_names:
        mismatches.append(
            f"surface names differ: missing={expected_names - actual_names} "
            f"extra={actual_names - expected_names}"
        )

    def resolve_names(coll: "JAG2GLM.MdxmSurfaceDataCollection", indices: List[int]) -> Set[str]:
        return {_surface_name(coll, i) for i in indices}

    for name in sorted(actual_names & expected_names):
        actual_surf = actual_by_name[name]
        expected_surf = expected_by_name[name]

        actual_parent = _surface_name(actual_coll, actual_surf.parentIndex) if actual_surf.parentIndex != -1 else None
        expected_parent = _surface_name(expected_coll, expected_surf.parentIndex) if expected_surf.parentIndex != -1 else None
        if actual_parent != expected_parent:
            mismatches.append(f"surface '{name}': parent differs: actual={actual_parent} expected={expected_parent}")

        actual_children = resolve_names(actual_coll, actual_surf.children)
        expected_children = resolve_names(expected_coll, expected_surf.children)
        if actual_children != expected_children:
            mismatches.append(f"surface '{name}': children differ: actual={actual_children} expected={expected_children}")

        if actual_surf.flags != expected_surf.flags:
            mismatches.append(f"surface '{name}': flags differ: actual={actual_surf.flags} expected={expected_surf.flags}")

        actual_shader = _decode(actual_surf.shader)
        expected_shader = _decode(expected_surf.shader)
        if actual_shader != expected_shader:
            mismatches.append(f"surface '{name}': shader differs: actual='{actual_shader}' expected='{expected_shader}'")

    if actual.header.numBones != expected.header.numBones:
        mismatches.append(f"numBones differs: actual={actual.header.numBones} expected={expected.header.numBones}")

    actual_lods = actual.LODCollection.LODs
    expected_lods = expected.LODCollection.LODs
    if len(actual_lods) != len(expected_lods):
        mismatches.append(f"LOD count differs: actual={len(actual_lods)} expected={len(expected_lods)}")

    for lod_index, (actual_lod, expected_lod) in enumerate(zip(actual_lods, expected_lods)):
        actual_surfs_by_name = {_surface_name(actual_coll, s.index): s for s in actual_lod.surfaces}
        expected_surfs_by_name = {_surface_name(expected_coll, s.index): s for s in expected_lod.surfaces}
        for name in sorted(set(actual_surfs_by_name) & set(expected_surfs_by_name)):
            a = actual_surfs_by_name[name]
            e = expected_surfs_by_name[name]
            if a.numVerts != e.numVerts:
                mismatches.append(f"LOD {lod_index} surface '{name}': numVerts differs: actual={a.numVerts} expected={e.numVerts}")
            if a.numTriangles != e.numTriangles:
                mismatches.append(f"LOD {lod_index} surface '{name}': numTriangles differs: actual={a.numTriangles} expected={e.numTriangles}")
            if a.numBoneReferences != e.numBoneReferences:
                mismatches.append(f"LOD {lod_index} surface '{name}': numBoneReferences differs: actual={a.numBoneReferences} expected={e.numBoneReferences}")

    return mismatches


def _bone_name(bones: List["JAG2GLA.MdxaBone"], index: int) -> Optional[str]:
    return bones[index].name if index != -1 else None


def compare_gla(
    actual: "JAG2GLA.GLA", expected: "JAG2GLA.GLA", translation_atol: float = 0.05, rotation_atol: float = 1e-3
) -> List[str]:
    """Structural bone hierarchy + numeric (tolerant) animation comparison of two JAG2GLA.GLA objects."""
    mismatches = []

    actual_bones = actual.skeleton.bones
    expected_bones = expected.skeleton.bones
    actual_by_name = {b.name: b for b in actual_bones}
    expected_by_name = {b.name: b for b in expected_bones}

    actual_names = set(actual_by_name)
    expected_names = set(expected_by_name)
    if actual_names != expected_names:
        mismatches.append(
            f"bone names differ: missing={expected_names - actual_names} "
            f"extra={actual_names - expected_names}"
        )

    common_names = actual_names & expected_names

    for name in sorted(common_names):
        actual_bone = actual_by_name[name]
        expected_bone = expected_by_name[name]

        actual_parent = _bone_name(actual_bones, actual_bone.parent)
        expected_parent = _bone_name(expected_bones, expected_bone.parent)
        if actual_parent != expected_parent:
            mismatches.append(f"bone '{name}': parent differs: actual={actual_parent} expected={expected_parent}")

        actual_children = {actual_bones[i].name for i in actual_bone.children}
        expected_children = {expected_bones[i].name for i in expected_bone.children}
        if actual_children != expected_children:
            mismatches.append(f"bone '{name}': children differ: actual={actual_children} expected={expected_children}")

    if actual.header.numFrames != expected.header.numFrames:
        mismatches.append(f"numFrames differs: actual={actual.header.numFrames} expected={expected.header.numFrames}")

    num_frames = min(actual.header.numFrames, expected.header.numFrames)
    for frame_index in range(num_frames):
        for name in sorted(common_names):
            actual_matrix = _bone_offset_matrix(actual, frame_index, name)
            expected_matrix = _bone_offset_matrix(expected, frame_index, name)
            for row in range(3):
                for col in range(4):
                    a = actual_matrix[row][col]
                    e = expected_matrix[row][col]
                    atol = translation_atol if col == 3 else rotation_atol
                    if abs(a - e) > atol:
                        mismatches.append(
                            f"frame {frame_index} bone '{name}': offset[{row}][{col}] differs: "
                            f"actual={a:.6f} expected={e:.6f} (atol={atol})"
                        )

    return mismatches


def _bone_offset_matrix(gla: "JAG2GLA.GLA", frame_index: int, bone_name: str) -> "mathutils.Matrix":
    bone_index = gla.boneIndexByName[bone_name]
    pool_index = gla.animation.frames[frame_index].boneIndices[bone_index]
    bone = cast("JAG2Math.CompBone", gla.animation.bonePool.bones[pool_index])
    return bone.matrix
