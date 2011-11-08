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

from . import mrw_g2_stringhelpers, mrw_g2_filesystem, mrw_g2_constants, mrw_g2_gla, mrw_g2_materialmanager
import struct, bpy

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
        self.name, self.animName = struct.unpack("64s64s", file.read(mrw_g2_constants.MAX_QPATH*2))
        #4x is 4 ignored bytes - the animIndex which is only used ingame
        self.numBones, self.numLODs, self.ofsLODs, self.numSurfaces, self.ofsSurfHierarchy, self.ofsEnd = struct.unpack("4x6i", file.read(4*7))
        return True, ""
    
    def saveToFile(self, file):
        # 0 is animIndex, only used ingame
        file.write(struct.pack("4si64s64s7i", mrw_g2_constants.GLM_IDENT, mrw_g2_constants.GLM_VERSION, self.name, self.animName, 0, self.numBones, self.numLODs, self.ofsLODs, self.numSurfaces, self.ofsSurfHierarchy, self.ofsEnd))
        return True, ""
    
    @classmethod
    def getSize():
        # 2 ints, 2 string, 7 ints
        return 2*4 + 2*64 + 7*4

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
        self.name, self.flags, self.shader = struct.unpack("64sI64s", file.read(64+4+64))
        # ignoring shaderIndex which is only used ingame
        self.parentIndex, self.numChildren = struct.unpack("4x2i", file.read(3*4))
        for i in range(self.numChildren):
            self.children.append(struct.unpack("i", file.read(4))[0])
    
    def saveToFile(self, file):
        # 0 is the shader index, only used ingame
        file.write(struct.pack("64sI64s3i", self.name, self.flags, self.shader, 0, self.parentIndex, self.numChildren))
        for i in range(self.numChildren):
            file.write(struct.pack("i", self.children[i]))
    
    @classmethod
    def getSize():
        # string, int, string, 4 ints
        return 64 + 4 + 64 + 4*4

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
    
    def getSize(self):
        return len(self.surfaces) * MdxmSurfaceData.getSize()

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
    #uv :: [int, int] (blender style, will be y-flipped)
    #groupLookup :: { int -> int } (object group index -> surface bone index pool index)
    def loadFromBlender(self, vertex, uv, groupLookup):
        for i in range(3):
            self.co.append(vertex.co[i])
            self.normal.append(vertex.normal[i])
            return True, ""
        
        self.uv[0] = uv[0]
        self.uv[1] = 1-uv[1] #flip Y
        
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
        self.indices = [] #order gets reversed during load/save
    
    def loadFromFile(self, file):
        self.indices.extend(struct.unpack("3i", file.read(3*4)))
        temp = self.indices[0]
        self.indices[0] = self.indices[2]
        self.indices[2] = temp
    
    def saveToFile(self, file):
        file.write(struct.pack("3i", self.indices[2], self.indices[1], self.indices[0]))

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
    
    # returns the created object
    def saveToBlender(self, data, lodLevel):
        #  retrieve metadata (same across LODs)
        surfaceData = data.surfaceDataCollection.surfaces[self.index]
        # blender won't let us create multiple things with the same name, so we add a LOD-suffix
        name =  mrw_g2_stringhelpers.decode(surfaceData.name)
        blenderName = name + "_" + str(lodLevel)
        
        #  create mesh
        mesh = bpy.data.meshes.new(blenderName)
        
        #create vertices
        mesh.vertices.add(self.numVerts)
        for i, bvert in enumerate(mesh.vertices):
            vert = self.vertices[i]
            bvert.co = vert.co
            bvert.normal = vert.normal
        
        #create faces
        mesh.faces.add(self.numTriangles)
        for i, face in enumerate(mesh.faces):
            tri = self.triangles[i]
            face.vertices = tri.indices
        
        #create uv coordinates
        mesh.uv_textures.new()
        uv_faces = mesh.uv_textures.active.data[:]
        for i, uv_face in enumerate(uv_faces):
            tri = self.triangles[i]
            uv_face.uv1 = self.vertices[tri.indices[0]].uv
            uv_face.uv1[1] = 1 - uv_face.uv1[1] #flip y
            uv_face.uv2 = self.vertices[tri.indices[1]].uv
            uv_face.uv2[1] = 1 - uv_face.uv2[1]
            uv_face.uv3 = self.vertices[tri.indices[2]].uv
            uv_face.uv3[1] = 1 - uv_face.uv3[1]
        
        mesh.validate()
        mesh.update()
        
        #  create object
        obj = bpy.data.objects.new(blenderName, mesh)
        
        #  create vertex groups (indices will match)
        for index in self.boneReferences:
            obj.vertex_groups.new(data.boneNames[index])
        
        #set weights
        for vertIndex, vert in enumerate(self.vertices):
            for weightIndex in range(vert.numWeights):
                obj.vertex_groups[vert.boneIndices[weightIndex]].add([vertIndex], vert.weights[weightIndex], 'ADD')
        
        #link object to scene
        bpy.context.scene.objects.link(obj)
        
        #make object active - needed for this smoothing operator and possibly for material adding later
        bpy.context.scene.objects.active = obj
        #smooth
        #todo smooth does not work
        bpy.ops.object.shade_smooth()
        #set material
        material = data.materialManager.getMaterial(name, surfaceData.shader)
        if material:
            bpy.ops.object.material_slot_add()
            obj.material_slots[0].material = material
            
        #set ghoul2 specific properties
        obj.g2_prop_name = name
        obj.g2_prop_tag = surfaceData.flags & mrw_g2_constants.SURFACEFLAG_TAG
        obj.g2_prop_off = surfaceData.flags & mrw_g2_constants.SURFACEFLAG_OFF
        
        # return object so hierarchy etc. can be set
        return obj
    
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
    
    def saveToBlender(self, data, root):
        # 1st pass: create objects
        objects = []
        for surface in self.surfaces:
            obj = surface.saveToBlender(data, self.level)
            objects.append(obj)
        # 2nd pass: set parent relations
        for i, obj in enumerate(objects):
            parentIndex = data.surfaceDataCollection.surfaces[i].parentIndex
            parent = root
            if parentIndex != -1:
                parent = objects[parentIndex]
            obj.parent = parent
    
    #fills self.surfaceOffsets and self.ofsEnd based on self.surfaces (must be initialized)
    def _calculateOffsets(self):
        self.surfaceOffsets = []
        baseOffset = 0
        for surface in self.surfaces:
            self.surfaceOffsets.append(baseOffset)
            baseOffset += surface.ofsEnd # = size
        # 1 int header, 1 int offset for each surface
        self.ofsEnd = baseOffset + 4 + 4 * len(self.surfaces)
    
    def getSize(self):
        size = 0
        for surface in self.surfaces:
            size += surface.ofsEnd

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
    
    def saveToBlender(self, data):
        for i, LOD in enumerate(self.LODs):
            root = bpy.data.objects.new("model_root_" + str(i), None)
            root.parent = data.scene_root
            bpy.context.scene.objects.link(root)
            LOD.saveToBlender(data, root)
    
    def getSize(self):
        size = 0
        for LOD in self.LODs:
            size += LOD.ofsEnd
        return size

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
    
    def loadFromBlender(self, glm_filepath_rel, gla_filepath_rel, basepath):
        self.header.name = glm_filepath_rel.encode()
        self.header.animName = gla_filepath_rel.encode()
        # create BoneName->BoneIndex lookup table based on GLA file (keeping in mind it might be "*default"/"")
        defaultSkeleton = (gla_filepath_rel == "" or gla_filepath_rel == "*default")
        if defaultSkeleton:
            self.header.numBones = 1
        else:
            boneIndexMap, message = buildBoneIndexLookupMap(mrw_g2_filesystem.RemoveExtension(mrw_g2_filesystem.AbsPath(gla_filepath_rel, basepath)) + ".gla")
            if boneIndexMap == False:
                return False, message
            self.header.numBones = len(boneIndexMap)
            # check if skeleton matches the specified one
            #TODO
            
        # load from Blender
        #TODO
        # calculate offsets etc.
        self._calculateHeaderOffsets()
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
    
    #calculates the offsets & counts saved in the header based on the rest
    def _calculateHeaderOffsets(self):
        # offset of "after header"
        baseOffset = MdxmHeader.getSize()
        # offset of "after hierarchy offset list"
        self.header.numSurfaces = len(self.surfaceDataOffsets.offset)
        baseOffset += 4 * self.header.numSurfaces
        # first "hierarchy" entry comes here
        self.header.ofsSurfHierarchy = baseOffset
        baseOffset += self.surfaceDataCollection.getSize()
        # first LOD comes here
        self.header.ofsLODs = baseOffset
        baseOffset += self.LODCollection.getSize()
        # that's everything, we've reached the end.
        self.header.ofsEnd = baseOffset
    
    # basepath: ../GameData/.../
    # gla: mrw_g2_gla.GLA object - the Skeleton (for weighting purposes)
    # scene_root: "scene_root" object in Blender
    def saveToBlender(self, basepath, gla, scene_root, skin_rel, guessTextures):
        class GeneralData:
            pass
        data = GeneralData()
        data.gla = gla
        data.scene_root = scene_root
        data.surfaceDataCollection = self.surfaceDataCollection
        data.materialManager = mrw_g2_materialmanager.MaterialManager()
        data.boneNames = {}
        for bone in gla.skeleton.bones:
            data.boneNames[bone.index] = bone.name
        success, message = data.materialManager.init(basepath, skin_rel, guessTextures)
        if not success:
            return False, message
        
        self.LODCollection.saveToBlender(data)
        return True, ""
    
    def getRequestedGLA(self):
        #todo
        return mrw_g2_stringhelpers.decode(self.header.animName)