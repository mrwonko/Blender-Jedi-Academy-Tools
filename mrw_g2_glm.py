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

GLM_IDENT = b'2LGM'
GLM_VERSION = 3

class MdxmHeader:
    name = ""
    animName = ""
    numbones = -1
    numLODs = -1
    ofsLODs = -1
    numSurfaces = -1
    ofsSurfHierarchy = -1
    ofsEnd = -1
    
    def __init__(self):
        pass
    
    def loadFromFile(self, file):
        #todo
        return True, ""
    
    def saveToFile(self, file):
        #todo
        return True, ""

class GLM:
    header = MdxmHeader()
    
    def __init__(self):
        pass
    
    def loadFromFile(self, filepath_abs):
        #todo
        return True, ""
    
    def loadFromBlender(self, glm_filepath_rel, gla_filepath_rel, basepath, scene_root):
        self.header.name = glm_filepath_rel
        self.header.animName = gla_filepath_rel
        #todo
        return True, ""
    
    def saveToFile(self, filepath_abs):
        #todo
        return True, ""
    
    # basepath: ../GameData/.../
    # gla: mrw_g2_gla.GLA object - the Skeleton (for weighting purposes)
    # scene_root: "scene_root" object in Blender
    def saveToBlender(self, basepath, gla, scene_root):
        #todo
        return True, ""
    
    def getRequestedGLA(self):
        #todo
        return self.header.animName