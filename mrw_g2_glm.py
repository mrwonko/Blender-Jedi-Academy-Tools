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
        file.write(struct.pack("4si64s64s7i", mrw_g2_constants.GLM_IDENT, mrw_g2_constants.GLM_VERSION, self.name.encode(), self.animName.encode(), 0, self.numBones, self.numLODs, self.ofsLODs, self.numSurfaces, self.ofsSurfHierarchy, self.ofsEnd))
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
        file.write(struct.pack("64sI64s3i", self.name.encode(), self.flags, self.shader.encode(), 0, self.parentIndex, self.numChildren))
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

class MdxmVertex:
    def __init__(self):
        self.co = []
        self.normal = []
        self.uv = []
        self.numWeights = 1
        self.weights = []
        self.boneIndices = []
    
    # doesn't load UV since that comes later
    def loadFromFile(self, file):
        self.normal.extend(struct.unpack("3f", file.read(3*4)))
        self.co.extend(struct.unpack("3f", file.read(3*4)))
        #this is a packed structure that contains all kinds of things...
        packedStuff, = struct.unpack("I", file.read(4))
        #this is not the complete weights, parts of it are in the packed stuff
        weights = []
        weights.extend(struct.unpack("4B", file.read(4)))
        #packedStuff bits 31 & 30: weight count
        self.numWeights = (packedStuff>>30)+1
        #packedStuff bits 29 & 28: nothing
        #packedStuff bits 20f, 22f, 24f, 26f: weight overflow
        totalWeight = 0
        for i in range(self.numWeights):
            # add overflow bits to the weight (MSBs!)
            weights[i] = weights[i] | (((packedStuff>>(20+2*i)) & 0b11)<<8)
            # convert to float (0..1023 -> 0.0..1.0)
            weights[i] = weights[i] / 1023
            if i+1 < self.numWeights:
                totalWeight += weights[i]
                self.weights.append(weights[i])
            else: # i+1 == self.numWeights:
                self.weights.append(1 - totalWeight)
        #packedStuff 0-19: bone indices, 5 bit each
        for i in range(self.numWeights):
            self.boneIndices.append((packedStuff >> (5*i)) & 0b11111)
    
    #index: this surface's index
    #does not save UV (comes later)
    def saveToFile(self, file):
        #  pack the stuff that needs packing
        #num weights
        packedStuff = (self.numWeights - 1) << 30
        weights = [0, 0, 0, 0]
        for i in range(self.numWeights):
            #convert weight to 10 bit integer
            weight = round(self.weights[i] * 1023)
            #lower 8 bits
            weights[i] = weight & 0xff
            #higher 2 bits
            hiWeight = (weight & 0x300) >> 8
            packedStuff |= hiWeight << (20 + 2*i)
            #bone index - 5 bits
            index = (self.boneIndices[i]) & 0b11111
            packedStuff |= index << (5*i)
        file.write(struct.pack("6fI4B", self.normal[0], self.normal[1], self.normal[2], self.co[0], self.co[1], self.co[2], packedStuff, weights[0], weights[1], weights[2], weights[3]))
    
    #vertex :: Blender MeshVertex
    #uv :: [int, int]
    #groupLookup :: { int -> int } (object group index -> surface bone index pool index)
    def loadFromBlender(self, vertex, uv, groupLookup):
        for i in range(3):
            self.co.append(vertex.co[i])
            self.normal.append(vertex.normal[i])
            return True, ""
        
        self.uv = uv
        
        #weight/bone indices
        global g_defaultSkeleton
        if g_defaultSkeleton:
            self.weights.append[1.0]
            self.boneIndices.append[1]
            self.numWeights = 1
        
        class Weight:
            index = -1
            weight = -1
        
        #get weights
        weights = []
        for g in vertex.groups:
            if g.group in groupLookup: #is a bone group?
                w = Weight()
                w.index = groupLookup[g.group]
                w.weight = g.weight
                weights.append(w)
        
        # remove weights if more than 4
        while len(weights) > 4:
            minWeight = 1
            minIndex = 0
            for i, w in enumerate(weights):
                if w.weight < minWeight:
                    minWeight = w.weight
                    minIndex = i
            del weights[minIndex]
        
        # normalize weights (sum = 1)
        totalWeight = 0
        for w in weights:
            totalWeight += w.weight
        if totalWeight == 0:
            return False, "Unweighted vertex found!"
        for w in weights:
            self.weights.append(w.weight / totalWeight)
            self.boneIndices.append(w.index)
        return True, ""

class MdxmTriangle:
    def __init__(self):
        self.indices = []
    
    def loadFromFile(self, file):
        self.indices.extend(struct.unpack("3i", file.read(3*4)))
    
    def saveToFile(self, file):
        file.write(struct.pack("3i", self.indices[0], self.indices[1], self.indices[2]))

class MdxmSurface:
    def __init__(self):
        self.index = -1
        self.numVerts = -1
        self.ofsVerts = -1
        self.numTriangles = -1
        self.ofsTriangles = -1
        self.numBoneReferences = -1
        self.ofsBoneReferences = -1
        self.ofsEnd = -1 # = size
        self.vertices = []
        self.triangles = []
        self.boneReferences = [] #integers: bone indices. maximum of 32, thus can be stored in 5 bit in vertices, saves space.
    
    def loadFromFile(self, file):
        startPos = file.tell()
        #  load surface header
        #in the beginning I ignore the ident, which is usually 0 and shouldn't matter
        self.index, ofsHeader, self.numVerts, self.ofsVerts, self.numTriangles, self.ofsTriangles, self.numBoneReferences, self.ofsBoneReferences, self.ofsEnd = struct.unpack("4x9i", file.read(10*4))
        assert(ofsHeader == -startPos)
        
        #  load vertices
        file.seek(startPos + self.ofsVerts)
        for i in range(self.numVerts):
            vert = MdxmVertex()
            vert.loadFromFile(file)
            self.vertices.append(vert)
        #uv textures come later
        for vert in self.vertices:
            vert.uv.extend(struct.unpack("2f", file.read(2*4)))
        
        #  load triangles
        file.seek(startPos + self.ofsTriangles)
        for i in range(self.numTriangles):
            t = MdxmTriangle()
            t.loadFromFile(file)
            self.triangles.append(t)
        
        #  load bone references
        file.seek(startPos + self.ofsBoneReferences)
        assert(len(self.boneReferences) == 0)
        self.boneReferences.extend(struct.unpack(str(self.numBoneReferences)+"i", file.read(4*self.numBoneReferences)))
        
        if file.tell() != startPos + self.ofsEnd:
            print("Warning: Surface structure unordered (bone references not last) or read error")
            file.seek(startPos + self.ofsEnd)
    
    #todo: loadFromBlender (_calculateOffsets() at the end)
    
    def saveToFile(self, file):
        startPos = file.tell()
        #  write header (= this)
        #0 = ident
        file.write(struct.pack("10i", 0, self.index, -startPos, self.numVerts, self.ofsVerts, self.numTriangles, self.ofsTriangles, self.numBoneReferences, self.ofsBoneReferences, self.ofsEnd))
        
        # I don't know if triangles *have* to come first, but when I export they do, hence the assertions.
        
        #  write triangles
        assert(file.tell() == startPos + self.ofsTriangles)
        for tri in self.triangles:
            tri.saveToFile(file)
        
        #  write vertices
        assert(file.tell() == startPos + self.ofsVerts)
        # write packed part
        for vert in self.vertices:
            vert.saveToFile(file)
        # write UVs
        for vert in self.vertices:
            file.write(struct.pack("2f", vert.uv[0], vert.uv[1]))
        
        #  write bone indices
        assert(file.tell() == startPos + self.ofsBoneReferences)
        for ref in self.boneReferences:
            file.write(struct.pack("i", ref))
        
        assert(file.tell() == startPos + self.ofsEnd)
    
    # fill offset and number variables
    def _calculateOffsets(self):
        baseOffset = 10*4 # header: 4 ints
        #triangles
        self.ofsTriangles = baseOffset
        self.numTriangles = len(self.triangles)
        baseOffset += 3*4*self.numTriangles #3 ints
        #bone references
        self.ofsBoneReferences = baseOffset
        self.numBoneReferences = len(self.boneReferences)
        baseOffset += 4*self.numBoneReferences # 1 int each
        #vertices
        self.ofsVerts = baseOffset
        self.numVerts = len(self.vertices)
        baseOffset += 10*4*self.numVerts # 6 floats co/normal, 8 bytes packed, 2 floats UV
        #that's all the content, so we've got total size now.
        self.ofsEnd = baseOffset

class MdxmLOD:
    def __init__(self):
        self.surfaceOffsets = []
        self.level = -1
        self.surfaces = []
        self.ofsEnd = -1 # = size
    
    def loadFromFile(self, file, header):
        startPos = file.tell()
        self.ofsEnd, = struct.unpack("i", file.read(4))
        for i in range(header.numSurfaces):
            # surface offsets - they're relative to a structure after the one containing ofsEnd, so I need to add sizeof(int) to them later.
            self.surfaceOffsets.append(struct.unpack("i", file.read(4))[0])
        for surfaceIndex, offset in enumerate(self.surfaceOffsets):
            if file.tell() != startPos + offset + 4:
                print("Warning: Surface not completely read or unordered")
                file.seek(startPos + offset + 4)
            surface = MdxmSurface()
            surface.loadFromFile(file)
            assert(surface.index == surfaceIndex)
            self.surfaces.append(surface)
        assert(file.tell() == startPos + self.ofsEnd)
    
    #todo: loadFromBlender (_calculateOffsets() at the end
    
    def saveToFile(self, file):
        startPos = file.tell()
        # write ofsEnd
        file.write(struct.pack("i", self.ofsEnd))
        # write surface offsets
        for offset in self.surfaceOffsets:
            file.write(struct.pack("i", offset))
        # write surfaces
        for surface in self.surfaces:
            surface.saveToFile(file)
        # that's it, should've reached end.
        assert(file.tell() == startPos + self.ofsEnd)
    
    def loadFromBlender(self): #todo: parameters?
        #todo
        self._calculateOffsets()
    
    #fills self.surfaceOffsets and self.ofsEnd based on self.surfaces (must be initialized)
    def _calculateOffsets(self):
        self.surfaceOffsets = []
        baseOffset = 0
        for surface in self.surfaces:
            self.surfaceOffsets.append(baseOffset)
            baseOffset += surface.ofsEnd # = size
        # 1 int header, 1 int offset for each surface
        self.ofsEnd = baseOffset + 4 + 4 * len(self.surfaces)

class MdxmLODCollection:
    def __init__(self):
        self.LODs = []
    
    def loadFromFile(self, file, header):
        for i in range(header.numLODs):
            startPos = file.tell()
            curLOD = MdxmLOD()
            curLOD.loadFromFile(file, header)
            curLOD.level = i
            if file.tell() != startPos + curLOD.ofsEnd:
                print("Warning: Internal reading error or LODs not tightly packed!")
                file.seek(startPos + curLOD.ofsEnd)
            self.LODs.append(curLOD)
    
    def saveToFile(self, file):
        for LOD in self.LODs:
            LOD.saveToFile(file)

class GLM:
    def __init__(self):
        self.header = MdxmHeader()
        self.surfaceDataOffsets = MdxmSurfaceDataOffsets()
        self.surfaceDataCollection = MdxmSurfaceDataCollection()
        self.LODCollection = MdxmLODCollection()
    
    def loadFromFile(self, filepath_abs):
        # open file
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
        
        # load surfaces' information - seeks positon using surfaceDataOffsets
        self.surfaceDataCollection.loadFromFile(file, self.surfaceDataOffsets)
        
        # load LODs
        file.seek(self.header.ofsLODs)
        self.LODCollection.loadFromFile(file, self.header)
        
        #should be at the end now, if the structures are in the expected order.
        if file.tell() != self.header.ofsEnd:
            print("Warning: File not completely read or LODs not last structure in file. The former would be a problem, the latter wouldn't.")
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
        if mrw_g2_filesystem.FileExists(filepath_abs):
            print("Warning: File exists! Overwriting.")
        #open file
        try:
            file = open(filepath_abs, "wb")
        except IOError:
            print("Failed to open file for writing: ", filepath_abs, sep="")
            return False, "Could not open file!"
        #save header
        self.header.saveToFile(file)
        #save surface data offsets
        self.surfaceDataOffsets.saveToFile(file)
        #save surface ("hierarchy") data
        self.surfaceDataCollection.saveToFile(file)
        #save LODs to file
        self.LODCollection.saveToFile(file)
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