# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Main File containing the important definitions

from .mod_reload import reload_modules
reload_modules(locals(), __package__, ["JAFilesystem", "JAG2Constants", "JAG2GLM", "JAG2GLA"], [".error_types", ".casts"])  # nopep8

from typing import Optional, Tuple
from . import JAFilesystem
from . import JAG2Constants
from . import JAG2GLM
from . import JAG2GLA
from .error_types import ErrorMessage, NoError
from .casts import optional_cast

import bpy

_scene_root_counter = 0


def _next_scene_root_name() -> str:
    global _scene_root_counter
    while True:
        suffix = "" if _scene_root_counter == 0 else f"_{_scene_root_counter}"
        name = f"scene_root{suffix}"
        _scene_root_counter += 1
        if name not in bpy.data.objects:
            return name


class Scene:

    def __init__(self, basepath: str):
        self.basepath = basepath
        self.scale = 1.0
        self.glm: Optional[JAG2GLM.GLM] = None
        self.gla: Optional[JAG2GLA.GLA] = None
        self.loaded_glm_rel: Optional[str] = None

    # Fills scene from on GLM file
    def loadFromGLM(self, glm_filepath_rel: str) -> Tuple[bool, ErrorMessage]:
        success, glm_filepath_abs = JAFilesystem.FindFile(
            glm_filepath_rel, self.basepath, ["glm"])
        if not success:
            print("File not found: ", self.basepath +
                  glm_filepath_rel + ".glm", sep="")
            return False, ErrorMessage(f".glm file {glm_filepath_rel} not found in basepath ({self.basepath})")
        self.glm = JAG2GLM.GLM()
        success, message = self.glm.loadFromFile(glm_filepath_abs)
        if not success:
            return False, message
        self.loaded_glm_rel = glm_filepath_rel
        return True, NoError

    # Loads scene from on GLA file
    def loadFromGLA(self, gla_filepath_rel: str, loadAnimations=JAG2GLA.AnimationLoadMode.NONE, startFrame=0, numFrames=1) -> Tuple[bool, ErrorMessage]:
        # create default skeleton if necessary (doing it here is a bit of a hack)
        if gla_filepath_rel == "*default":
            self.gla = JAG2GLA.GLA()
            self.gla.header.numBones = 1
            self.gla.isDefault = True
            return True, NoError
        success, gla_filepath_abs = JAFilesystem.FindFile(
            gla_filepath_rel, self.basepath, ["gla"])
        if not success:
            print("File not found: ", self.basepath +
                  gla_filepath_rel + ".gla", sep="")
            return False, ErrorMessage(f".gla file {gla_filepath_rel} not found in basepath ({self.basepath})")
        self.gla = JAG2GLA.GLA()
        success, message = self.gla.loadFromFile(
            gla_filepath_abs, loadAnimations, startFrame, numFrames)
        if not success:
            return False, message
        return True, NoError

    # "Loads" model from Blender data
    def loadModelFromBlender(self, glm_filepath_rel, gla_filepath_rel):
        self.glm = JAG2GLM.GLM()
        success, message = self.glm.loadFromBlender(
            glm_filepath_rel, gla_filepath_rel, self.basepath)
        if not success:
            return False, message
        return True, ""

    # "Loads" skeleton & animation from Blender data
    def loadSkeletonFromBlender(self, gla_filepath_rel, gla_reference_rel):
        self.gla = JAG2GLA.GLA()
        gla_reference_abs = ""
        if gla_reference_rel != "":
            success, gla_reference_abs = JAFilesystem.FindFile(
                gla_reference_rel, self.basepath, ["gla"])
            if not success:
                return False, "Could not find reference GLA"
        success, message = self.gla.loadFromBlender(
            gla_filepath_rel, gla_reference_abs)
        if not success:
            return False, message
        return True, ""

    # saves the model to a .glm file
    def saveToGLM(self, glm_filepath_rel):
        glm_filepath_abs = JAFilesystem.AbsPath(
            glm_filepath_rel, self.basepath) + ".glm"
        success, message = optional_cast(JAG2GLM.GLM, self.glm).saveToFile(glm_filepath_abs)
        if not success:
            return False, message
        return True, ""

    # saves the skeleton & animations to a .gla file
    def saveToGLA(self, gla_filepath_rel):
        gla_filepath_abs = JAFilesystem.AbsPath(
            gla_filepath_rel, self.basepath) + ".gla"
        success, message = optional_cast(JAG2GLA.GLA, self.gla).saveToFile(gla_filepath_abs)
        if not success:
            return False, message
        return True, ""

    # "saves" the scene to blender
    # skeletonFixes is an enum with possible skeleton fixes - e.g. 'JKA' for connection- and
    def saveToBlender(self, scale, skin_rel, guessTextures: bool, useAnimation: bool, skeletonFixes: JAG2Constants.SkeletonFixes) -> Tuple[bool, ErrorMessage]:
        scene_root = bpy.data.objects.get("scene_root")
        created_scene_root = False
        if scene_root is None:
            scene_root_name = _next_scene_root_name()
            scene_root = bpy.data.objects.new(scene_root_name, None)
            scene_root.scale = (scale, scale, scale)
            created_scene_root = True
        normalized_glm = JAG2GLM._normalize_glm_path(self.loaded_glm_rel)
        if normalized_glm:
            scene_root.g2_prop_glm_name = normalized_glm
        if created_scene_root:
            bpy.context.scene.collection.objects.link(scene_root)
        elif scene_root.name not in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(scene_root)
        # there's always a skeleton (even if it's *default)
        success, message = optional_cast(JAG2GLA.GLA, self.gla).saveToBlender(
            scene_root, useAnimation, skeletonFixes)
        if not success:
            return False, message
        if self.glm:
            success, message = self.glm.saveToBlender(
                self.basepath, optional_cast(JAG2GLA.GLA, self.gla), scene_root, skin_rel, guessTextures)
            if not success:
                return False, message
        _merge_vertex_groups_if_needed()
        return True, NoError

    # returns the relative path of the gla file referenced in the glm header
    def getRequestedGLA(self) -> str:
        return optional_cast(JAG2GLM.GLM, self.glm).getRequestedGLA()


_VERTEX_GROUP_BASE_MAP = {
    "d1_j3": "d1_j2",
    "d3_j3": "d3_j2",
    "d3_j1": "d2_j1",
    "d3_j2": "d2_j2",
    "d4_j3": "d4_j2",
    "d5_j1": "d4_j1",
    "d5_j2": "d4_j2",
    "d5_j3": "d4_j2",
}

_VERTEX_GROUP_SPECIAL_MAP = {
    "ltarsal": "ltalus",
    "rtarsal": "rtalus",
    "mc5": "lhand",
    "mc7": "rhand",
}

_VERTEX_GROUP_PREFIXES = ("l_", "r_")


def _merge_vertex_group(obj: bpy.types.Object, src_name: str, dst_name: str) -> None:
    if src_name not in obj.vertex_groups:
        return

    if dst_name not in obj.vertex_groups:
        obj.vertex_groups.new(name=dst_name)

    vg_src = obj.vertex_groups[src_name]
    vg_dst = obj.vertex_groups[dst_name]

    mesh = obj.data

    for v in mesh.vertices:
        try:
            weight = vg_src.weight(v.index)
        except RuntimeError:
            continue

        vg_dst.add([v.index], weight, 'REPLACE')

    obj.vertex_groups.remove(vg_src)
    print(f"{obj.name}: {src_name} → {dst_name}")


def _merge_vertex_groups_if_needed() -> None:
    skeleton_root = bpy.data.objects.get("skeleton_root")
    if skeleton_root is None or skeleton_root.type != 'ARMATURE':
        return

    armature = skeleton_root.data
    run_conversion = False

    if "ltarsal" not in armature.bones:
        print("Jedi Academy skeleton in scene, converting model from jk2 to jka")
        run_conversion = True
    
    if not run_conversion:
        return

    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue

        for src, dst in _VERTEX_GROUP_BASE_MAP.items():
            for prefix in _VERTEX_GROUP_PREFIXES:
                _merge_vertex_group(obj, prefix + src, prefix + dst)

        for src, dst in _VERTEX_GROUP_SPECIAL_MAP.items():
            _merge_vertex_group(obj, src, dst)
