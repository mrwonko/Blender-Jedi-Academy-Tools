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
reload_modules(locals(), __package__, ["JAFilesystem", "JAG2AnimationCFG", "JAG2Constants", "JAG2GLM", "JAG2GLA"], [".error_types", ".casts"])  # nopep8

from typing import Optional, Tuple
from . import JAFilesystem
from . import JAG2Constants
from . import JAG2AnimationCFG
from . import JAG2GLM
from . import JAG2GLA
from .error_types import ErrorMessage, NoError
from .casts import optional_cast

import bpy


def findSceneRootObject() -> Optional[bpy.types.Object]:
    scene_root = None
    if "scene_root" in bpy.data.objects:
        # if so, use that
        scene_root = bpy.data.objects["scene_root"]
    return scene_root


class Scene:

    def __init__(self, basepath: str):
        self.basepath = basepath
        self.scale = 1.0
        self.glm: Optional[JAG2GLM.GLM] = None
        self.gla: Optional[JAG2GLA.GLA] = None
        self.animation_cfg: Optional[JAG2AnimationCFG.AnimationCGF] = None

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
        return True, NoError
    
    # Loads animations sequences from a CFG file
    def loadFromCFG(self, cfg_filepath: str) -> Tuple[bool, ErrorMessage]:
        self.animation_cfg = JAG2AnimationCFG.AnimationCGF()
        success, message = self.animation_cfg.load_from_cfg(cfg_filepath)
        if not success:
            self.animation_cfg = None
            return False, message
        return True, message

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
        # is there already a scene root in blender?
        scene_root = findSceneRootObject()
        if scene_root:
            # make sure it's linked to the current scene
            if not "scene_root" in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.link(scene_root)
        else:
            # create it otherwise
            scene_root = bpy.data.objects.new("scene_root", None)
            scene_root.scale = (scale, scale, scale)
            bpy.context.scene.collection.objects.link(scene_root)
        # there's always a skeleton (even if it's *default)
        success, message = optional_cast(JAG2GLA.GLA, self.gla).saveToBlender(
            scene_root, useAnimation, skeletonFixes, self.animation_cfg)
        if not success:
            return False, message
        if self.glm:
            success, message = self.glm.saveToBlender(
                self.basepath, optional_cast(JAG2GLA.GLA, self.gla), scene_root, skin_rel, guessTextures)
            if not success:
                return False, message
        return True, NoError

    # returns the relative path of the gla file referenced in the glm header
    def getRequestedGLA(self) -> str:
        return optional_cast(JAG2GLM.GLM, self.glm).getRequestedGLA()
