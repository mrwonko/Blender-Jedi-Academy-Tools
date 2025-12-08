# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####

from .mod_reload import reload_modules
reload_modules(
    locals(),
    __package__,
    [
        "JAG2Scene",      # <-- REQUIRED FIX (module must reload itself)
        "JAFilesystem",
        "JAG2Constants",
        "JAG2GLM",
        "JAG2GLA",
    ],
    [".error_types", ".casts"]
)

import bpy
from typing import Optional, Tuple
from . import JAFilesystem
from . import JAG2Constants
from . import JAG2GLM
from . import JAG2GLA
from .error_types import ErrorMessage, NoError
from .casts import optional_cast


# ----------------------------------------------------------
# Scene Root Helper
# ----------------------------------------------------------

def findSceneRootObject() -> Optional[bpy.types.Object]:
    return bpy.data.objects.get("scene_root")


# ----------------------------------------------------------
# Scene Logic
# ----------------------------------------------------------

class Scene:

    def __init__(self, basepath: str):
        self.basepath = basepath
        self.scale = 1.0
        self.glm: Optional[JAG2GLM.GLM] = None
        self.gla: Optional[JAG2GLA.GLA] = None

    # ------------------------------------------------------
    # Load GLM
    # ------------------------------------------------------
    def loadFromGLM(self, glm_filepath_rel: str) -> Tuple[bool, ErrorMessage]:
        success, glm_filepath_abs = JAFilesystem.FindFile(
            glm_filepath_rel, self.basepath, ["glm"]
        )
        if not success:
            return False, ErrorMessage(f".glm file {glm_filepath_rel} not found in basepath {self.basepath}")

        self.glm = JAG2GLM.GLM()
        return self.glm.loadFromFile(glm_filepath_abs)

    # ------------------------------------------------------
    # Load GLA
    # ------------------------------------------------------
    def loadFromGLA(self, gla_filepath_rel: str,
                    loadAnimations=JAG2GLA.AnimationLoadMode.NONE,
                    startFrame=0, numFrames=1) -> Tuple[bool, ErrorMessage]:

        # default skeleton
        if gla_filepath_rel == "*default":
            self.gla = JAG2GLA.GLA()
            self.gla.header.numBones = 1
            self.gla.isDefault = True
            return True, NoError

        success, gla_filepath_abs = JAFilesystem.FindFile(
            gla_filepath_rel, self.basepath, ["gla"]
        )
        if not success:
            return False, ErrorMessage(f".gla file {gla_filepath_rel} not found in basepath {self.basepath}")

        self.gla = JAG2GLA.GLA()
        return self.gla.loadFromFile(
            gla_filepath_abs, loadAnimations, startFrame, numFrames
        )

    # ------------------------------------------------------
    # Load Model from Blender
    # ------------------------------------------------------
    def loadModelFromBlender(self, glm_filepath_rel, gla_filepath_rel):
        self.glm = JAG2GLM.GLM()
        return self.glm.loadFromBlender(
            glm_filepath_rel, gla_filepath_rel, self.basepath
        )

    # ------------------------------------------------------
    # Load Skeleton from Blender
    # ------------------------------------------------------
    def loadSkeletonFromBlender(self, gla_filepath_rel, gla_reference_rel):
        self.gla = JAG2GLA.GLA()

        gla_reference_abs = ""
        if gla_reference_rel:
            success, gla_reference_abs = JAFilesystem.FindFile(
                gla_reference_rel, self.basepath, ["gla"]
            )
            if not success:
                return False, "Could not find reference GLA"

        success, message = self.gla.loadFromBlender(
            gla_filepath_rel, gla_reference_abs
        )
        return success, message

    # ------------------------------------------------------
    # Save GLM
    # ------------------------------------------------------
    def saveToGLM(self, glm_filepath_rel):
        glm_filepath_abs = JAFilesystem.AbsPath(
            glm_filepath_rel, self.basepath
        ) + ".glm"

        return optional_cast(JAG2GLM.GLM, self.glm).saveToFile(glm_filepath_abs)

    # ------------------------------------------------------
    # Save GLA
    # ------------------------------------------------------
    def saveToGLA(self, gla_filepath_rel):
        gla_filepath_abs = JAFilesystem.AbsPath(
            gla_filepath_rel, self.basepath
        ) + ".gla"

        return optional_cast(JAG2GLA.GLA, self.gla).saveToFile(gla_filepath_abs)

    # ------------------------------------------------------
    # Save Scene to Blender
    # ------------------------------------------------------
    def saveToBlender(self, scale, skin_rel, guessTextures: bool,
                      useAnimation: bool,
                      skeletonFixes: JAG2Constants.SkeletonFixes
                      ) -> Tuple[bool, ErrorMessage]:

        scene_root = findSceneRootObject()

        if scene_root:
            # ensure linked to ACTIVE collection
            coll = bpy.context.view_layer.active_layer_collection.collection
            if scene_root.name not in coll.objects:
                coll.objects.link(scene_root)
        else:
            scene_root = bpy.data.objects.new("scene_root", None)
            scene_root.scale = (scale, scale, scale)
            bpy.context.view_layer.active_layer_collection.collection.objects.link(scene_root)

        # Save GLA first
        success, message = optional_cast(JAG2GLA.GLA, self.gla).saveToBlender(
            scene_root, useAnimation, skeletonFixes
        )
        if not success:
            return False, message

        # Save GLM if it exists
        if self.glm:
            success, message = self.glm.saveToBlender(
                self.basepath,
                optional_cast(JAG2GLA.GLA, self.gla),
                scene_root,
                skin_rel,
                guessTextures
            )
            if not success:
                return False, message

        return True, NoError

    # ------------------------------------------------------
    # Return GLA Path from GLM Header
    # ------------------------------------------------------
    def getRequestedGLA(self) -> str:
        return optional_cast(JAG2GLM.GLM, self.glm).getRequestedGLA()

