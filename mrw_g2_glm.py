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

from . import mrw_g2_iohelpers, mrw_g2_filesystem, mrw_g2_constants, mrw_g2_gla
import struct

def buildBoneIndexLookupMap(gla_filepath_abs):
    print("Loading gla file for bone name -> bone index lookup")
    #open file
    try:
        file = open(gla_filepath_abs, mode="rb")
    except IOError:
        print("Could not open ", gla_filepath_abs, sep="")
        return False, "Could not open gla file for bone index lookup!"
    #read header
    header = mrw_g2_gla.MdxaHeader()
    success, message = header.loadFromFile(file)
    if not success:
        return False, message
    #read offsets
    boneOffsets = mrw_g2_gla.MdxaBoneOffsets()
    boneOffsets.loadFromFile(file, header.numBones) #cannot fail (except with exception)
    #read skeleton
    skeleton = mrw_g2_gla.MdxaSkel()
    skeleton.loadFromFile(file, boneOffsets)
    #build lookup map
    boneIndices = {}
    for bone in skeleton.bones:
        boneIndices[bone.name] = bone.index
    return boneIndices, "all right"

class MdxmHeader:
    
    def __init__(self):
        self.name = ""
        self.animName = ""
        self.numBones = -1
        self.numLODs = -1
        self.ofsLODs = -1
        self.numSurfaces = -1
        self.ofsSurfHierarchy = -1
        self.ofsEnd = -1
    
    def loadFromFile(self, file):
        #ident check
        ident, = struct.unpack("4s", file.read(4))
        if ident != mrw_g2_constants.GLM_IDENT:
            print("File does not start with ", mrw_g2_constants.GLM_IDENT, " but ", ident, " - no GLM!")
            return False, "Is no GLM file!"
        #version check
        version, = struct.unpack("i", file.read(4))
        if version != mrw_g2_constants.GLM_VERSION:
            return False, "Wrong glm file version! ("+str(version)+" should be "+str(mrw_g2_constants.GLM_VERSION)+")"
        # read data
        self.name = mrw_g2_iohelpers.toQ3String(file.read(mrw_g2_constants.MAX_QPATH))
        self.animName = mrw_g2_iohelpers.toQ3String(file.read(mrw_g2_constants.MAX_QPATH))
        #4x is 4 ignored bytes - the animIndex which is only used ingame
        self.numBones, self.numLODs, self.ofsLODs, self.numSurfaces, self.ofsSurfHierarchy, self.ofsEnd = struct.unpack("4x6i", file.read(4*7))
        return True, ""
    
    def saveToFile(self, file):
        # 0 is animIndex, only used ingame
        file.write(struct.pack("4si64s64s7i", mrw_g2_constants.GLM_IDENT, mrw_g2_constants.GLM_VERSION, self.name, self.animName, 0, self.numBones, self.numLODs, self.ofsLODs, self.numSurfaces, self.ofsSurfHierarchy, self.ofsEnd))
        return True, ""

# offsets of the surface data
class MdxmSurfaceDataOffsets:
    def __init__(self):
        self.baseOffset = 2*4 + 2*64 + 7*4 #always directly after the header, which is this big.
        self.offsets = []
    
    def loadFromFile(self, file, numSurfaces):
        assert(self.baseOffset == file.tell())
        for i in range(numSurfaces):
            self.offsets.append(struct.unpack("i", file.read(4))[0])
    
    def saveToFile(self, file):
        for offset in self.offsets:
            file.write(struct.pack("i", offset))
    
    # returns the size of this in bytes (when written to file)
    def getSize():
        return 4 * len(self.offsets)

# originally called mdxmSurfaceHierarchy_t, I think that name is misleading (but mine's not too good, either)
class MdxmSurfaceData:
    def __init__(self):
        self.name = ""
        self.flags = -1
        self.shader = ""
        self.parentIndex = -1
        self.numChildren = -1
        self.children = []
        self.index = -1 #filled by MdxmSurfaceHierarchy.loadFromFile, not saved
    
    def loadFromFile(self, file):
        self.name = mrw_g2_iohelpers.toQ3String(file.read(mrw_g2_constants.MAX_QPATH))
        self.flags, = struct.unpack("I", file.read(4))
        self.shader = mrw_g2_iohelpers.toQ3String(file.read(mrw_g2_constants.MAX_QPATH))
        # ignoring shaderIndex which is only used ingame
        self.parentIndex, self.numChildren = struct.unpack("4x2i", file.read(3*4))
        for i in range(self.numChildren):
            self.children.append(struct.unpack("i", file.read(4))[0])
    
    def saveToFile(self, file):
        # 0 is the shader index, only used ingame
        file.write(struct.pack("64sI64s3i", self.name, self.flags, self.shader, 0, self.parentIndex, self.numChildren))
        for i in range(self.numChildren):
            file.write(struct.pack("i", self.children[i]))

# all the surface hierarchy/shader/name/flag/... information entries (MdxmSurfaceInfo)
class MdxmSurfaceDataCollection:
    def __init__(self):
        self.surfaces = []
    
    def loadFromFile(self, file, surfaceInfoOffsets):
        for i, offset in enumerate(surfaceInfoOffsets.offsets):
            file.seek(surfaceInfoOffsets.baseOffset + offset)
            surfaceInfo = MdxmSurfaceData()
            surfaceInfo.loadFromFile(file)
            surfaceInfo.index = i
            self.surfaces.append(surfaceInfo)
    
    def saveToFile(self, file):
        for surfaceInfo in self.surfaces:
            surfaceInfo.saveToFile(file)

class GLM:
    
    def __init__(self):
        self.header = MdxmHeader()
        self.surfaceDataOffsets = MdxmSurfaceDataOffsets()
        self.surfaceDataCollection = MdxmSurfaceDataCollection()
    
    def loadFromFile(self, filepath_abs):
        try:
            file = open(filepath_abs, mode = "rb")
        except IOError:
            print("Could not open file: ", filepath_abs, sep="")
            return False, "Could not open file"
        success, message = self.header.loadFromFile(file)
        if not success:
            return False, message
        # load surface hierarchy offsets
        self.surfaceDataOffsets.loadFromFile(file, self.header.numSurfaces)
        # load surfaces' information
        self.surfaceDataCollection.loadFromFile(file, self.surfaceDataOffsets)
        #todo
        # load LODs
        return True, ""
    
    def loadFromBlender(self, glm_filepath_rel, gla_filepath_rel, basepath, scene_root):
        self.header.name = glm_filepath_rel
        self.header.animName = gla_filepath_rel
        #todo
        # create BoneName->BoneIndex lookup table based on GLA file (keeping in mind it might be "*default"/"")
        defaultSkeleton = gla_filepath_rel == "" or gla_filepath_rel == "*default"
        if not defaultSkeleton:
            boneIndexMap, message = buildBoneIndexLookupMap(mrw_g2_filesystem.RemoveExtension(mrw_g2_filesystem.AbsPath(gla_filepath_rel, basepath)) + ".gla")
            if boneIndexMap == False:
                return False, message
        print("== bone lookup map ==")
        print(boneIndexMap)
        # load from Blender
        # calculate offsets etc.
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