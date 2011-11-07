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

from . import mrw_g2_iohelpers, mrw_g2_constants, mrw_g2_math
import struct

class MdxaHeader:
    
    def __init__(self):
        self.name = ""
        self.scale = 0
        self.numFrames = -1
        self.ofsFrames = -1
        self.numBones = -1
        self.ofsCompBonePool = -1
        self.ofsSkel = -1 # this is also MdxaSkelOffsets.baseOffset + MdxaSkelOffsets.boneOffsets[0] - probably a historic leftover
        self.ofsEnd = -1
    
    def loadFromFile(self, file):
        # check ident
        ident, = struct.unpack("4s", file.read(4))
        if ident != mrw_g2_constants.GLA_IDENT:
            print("File does not start with ", mrw_g2_constants.GLA_IDENT, " but ", ident, " - no GLA!")
            return False, "Is no GLA file!"
        version, = struct.unpack("i", file.read(4))
        if version != mrw_g2_constants.GLA_VERSION:
            return False, "Wrong gla file version! ("+str(version)+" should be "+str(mrw_g2_constants.GLA_VERSION)+")"
        name = mrw_g2_iohelpers.toQ3String(file.read(mrw_g2_constants.MAX_QPATH))
        self.scale, self.numFrames, self.numBones, self.numBones, self.ofsCompBonePool, self.ofsSkel, self.ofsEnd = struct.unpack("f6i", file.read(7*4))
        return True, ""

class MdxaBoneOffsets:
    
    def __init__(self):
        self.baseOffset = 2*4 + 64 + 4*7 #sizeof header
        self.boneOffsets = []
    
    # fail-safe (except exceptions)
    def loadFromFile(self, file, numBones):
        assert(self.baseOffset == file.tell())
        for i in range(numBones):
            self.boneOffsets.append(struct.unpack("i", file.read(4))[0])

# originally called MdxaSkel_t, but I find that name misleading
class MdxaBone:
    def __init__(self):
        self.name = ""
        self.flags = -1
        self.parent = -1
        self.basePoseMat = mrw_g2_math.Matrix()
        self.basePoseMatInv = mrw_g2_math.Matrix()
        self.numChildren = -1
        self.children = []
        self.index = -1 # not saved, filled by loadBonesFromFile()
    
    def loadFromFile(self, file):
        self.name = mrw_g2_iohelpers.toQ3String(file.read(mrw_g2_constants.MAX_QPATH))
        self.flags, self.parent = struct.unpack("Ii", file.read(2*4))
        self.basePoseMat.loadFromFile(file)
        self.basePoseMatInv.loadFromFile(file)
        self.numChildren, = struct.unpack("i", file.read(4))
        for i in range(self.numChildren):
            self.children.append(struct.unpack("i", file.read(4))[0])

class MdxaSkel:
    def __init__(self):
        self.bones = []
    
    def loadFromFile(self, file, offsets):
        for i, offset in enumerate(offsets.boneOffsets):
            file.seek(offsets.baseOffset + offset)
            bone = MdxaBone()
            bone.loadFromFile(file)
            bone.index = i
            self.bones.append(bone)

class GLA:
    
    def __init__(self):
        #whether this is the automatic default skeleton
        self.isDefault = False
        self.header = MdxaHeader()
        self.boneOffsets = MdxaBoneOffsets()
        self.skeleton = MdxaSkel()
        self.boneIndexByName = {}
        # boneNameByIndex = {} #just use bones[index].name
    
    def loadFromFile(self, filepath_abs):
        try:
            file = open(filepath_abs, mode="rb")
        except IOError:
            print("Could not open file: ", filepath_abs, sep="")
            return False, "Could not open file!"
        # load header
        success, message = self.header.loadFromFile(file)
        if not success:
            return False, message
        # load offsets (directly after header, always)
        self.boneOffsets.loadFromFile(file, self.header.numBones)
        # load bones
        self.skeleton.loadFromFile(file, self.boneOffsets)
        # build lookup map
        for bone in self.skeleton.bones:
            self.boneIndexByName[bone.name] = bone.index
        #todo
        return True, ""
    
    def loadFromBlender(self, gla_filepath_rel, scene_root):
        #todo
        return True, ""
    
    def saveToFile(self, filepath_abs):
        #todo
        return True, ""
    
    def saveToBlender(self, scene_root):
        #todo
        return True, ""
