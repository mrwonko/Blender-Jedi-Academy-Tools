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

from . import mrw_g2_filesystem

class Scene:
    scale = 1.0
    
    def __init__(self):
        pass
    
    # Fills scene from on GLM file
    def loadFromGLM(self, filename_rel, basepath, scale=1.0):
        self.scale = scale
        #todo
        print("TODO: load GLM ", filename_rel, " (basepath ", basepath, ")", sep="");
        success, filename_abs = mrw_g2_filesystem.FindFile(filename_rel, basepath, ["glm"])
        if not success:
            print("File not found: ", basepath + filename_rel + ".glm", sep="")
            return False, "File not found! (no .glm?)"
        return True, ""
    
    # Loads scene from on GLA file
    def loadFromGLA(self, filename_rel, basepath, scale=1.0, loadAnimations=False):
        self.scale = scale
        #todo
        print("TODO: load GLA ", filename_rel, " (basepath ", basepath, ", animations = ", loadAnimations, ")", sep="");
        success, filename_abs = mrw_g2_filesystem.FindFile(filename_rel, basepath, ["gla"])
        if not success:
            print("File not found: ", basepath + filename_rel + ".gla", sep="")
            return False, "File not found! (no .gla?)"
        return True, ""
    
    # "Loads" model from Blender data
    def loadModelFromBlender(self):
        #todo
        print("TODO: load model from blender")
        return True, ""
    
    # "Loads" skeleton & animation from Blender data
    def loadSkeletonFromBlender(self):
        #todo
        print("TODO: load skeleton from blender")
        return True, ""
    
    #saves the model to a .glm file
    def saveToGLM(self, filename_rel, basepath, glafile_rel):
        #todo
        print("TODO: Save to ", filename_rel, ".glm (basepath: ", basepath, ", gla file: ", glafile_rel, ")", sep="")
        filename_abs = mrw_g2_filesystem.AbsPath(filename_rel, basepath) + ".glm"
        return True, ""
    
    # saves the skeleton & animations to a .gla file
    def saveToGLA(self, filename_rel, basepath):
        #todo
        print("TODO: Save to ", filename_rel, ".gla (basepath: ", basepath, ")", sep="")
        filename_abs = mrw_g2_filesystem.AbsPath(filename_rel, basepath) + ".gla"
        return True, ""
    
    # "saves" the scene to blender
    def saveToBlender(self):
        #todo
        print("TODO: Saving to blender")
        return True, ""
    
    # returns the relative path of the gla file referenced in the glm header
    def getRequestedGLA(self):
        #todo: load from GLM
        return "models/players/_humanoid/_humanoid"
