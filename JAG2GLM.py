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


from .mod_reload import reload_modules
reload_modules(locals(), __package__, ["JAStringhelper", "JAFilesystem", "JAG2Constants", "JAG2GLA", "JAMaterialmanager", "MrwProfiler", "JAG2Panels"], [".casts", ".error_types"])  # nopep8

from dataclasses import dataclass
from typing import BinaryIO, Dict, List, Optional, Sequence, Tuple, cast
import struct
from . import JAStringhelper
from . import JAFilesystem
from . import JAG2Constants
from . import JAG2GLA
from . import JAMaterialmanager
from . import MrwProfiler
from . import JAG2Panels
from .casts import optional_cast, downcast, bpy_generic_cast, optional_list_cast, unpack_cast, matrix_getter_cast, vector_getter_cast, vector_overload_cast
from .error_types import ErrorMessage, NoError

import bpy
import mathutils


BoneIndexMap = Dict[str, int]


def buildBoneIndexLookupMap(gla_filepath_abs: str) -> Tuple[Optional[BoneIndexMap], ErrorMessage]:
    print("Loading gla file for bone name -> bone index lookup")
    # open file
    try:
        file = open(gla_filepath_abs, mode="rb")
    except IOError:
        print("Could not open ", gla_filepath_abs, sep="")
        return None, ErrorMessage("Could not open gla file for bone index lookup!")
    # read header
    header = JAG2GLA.MdxaHeader()
    success, message = header.loadFromFile(file)
    if not success:
        return None, message
    # read offsets
    boneOffsets = JAG2GLA.MdxaBoneOffsets()
    # cannot fail (except with exception)
    boneOffsets.loadFromFile(file, header.numBones)
    # read skeleton
    skeleton = JAG2GLA.MdxaSkel()
    skeleton.loadFromFile(file, boneOffsets)
    # build lookup map
    boneIndices: Dict[str, int] = {}
    for bone in skeleton.bones:
        boneIndices[bone.name] = bone.index
    return boneIndices, NoError


def getName(object: bpy.types.Object) -> str:
    if object.g2_prop_name != "":  # pyright: ignore [reportAttributeAccessIssue]
        return object.g2_prop_name  # pyright: ignore [reportAttributeAccessIssue]
    return object.name


class GetBoneWeightException(Exception):
    pass


def getBoneWeights(vertex: bpy.types.MeshVertex, meshObject: bpy.types.Object, armatureObject: bpy.types.Object, maxBones: int = -1):
    # find the armature modifier
    modifier = None
    for mod in meshObject.modifiers:
        if mod.type == 'ARMATURE':
            if modifier != None:
                raise GetBoneWeightException(
                    f"Multiple armature modifiers on {meshObject.name}!")
            modifier = mod
    if modifier == None:
        raise GetBoneWeightException(
            f"{meshObject.name} has no armature modifier!")
    armature = downcast(bpy.types.Armature, armatureObject.data)

    # this will eventually contain the weights per bone (by name) if not 0
    weights: Dict[str, float] = {}

    # vertex groups take priority
    if modifier.use_vertex_groups:
        for group in vertex.groups:
            group = bpy_generic_cast(bpy.types.VertexGroupElement, group)
            weight = group.weight
            index = group.group
            name = meshObject.vertex_groups[index].name
            if weight > 0 and name in armature.bones:
                weights[name] = weight

    # if there are vertex group weights, envelopes are ignored
    if len(weights) == 0 and modifier.use_bone_envelopes:
        co_meshspace = vector_getter_cast(vertex.co)
        co_worldspace = vector_overload_cast(matrix_getter_cast(meshObject.matrix_world) @ co_meshspace)
        co_armaspace = vector_overload_cast(matrix_getter_cast(armatureObject.matrix_world).inverted() @ co_worldspace)
        for bone in armature.bones:
            bone = bpy_generic_cast(bpy.types.Bone, bone)
            weight = bone.evaluate_envelope(co_armaspace)
            if weight > 0:
                weights[bone.name] = weight

    # remove smallest weight while there are more than allowed
    if maxBones != -1:
        while len(weights) > maxBones:
            minKey, _ = min(weights.items(), key=lambda i: i[1])
            del weights[minKey]

    # if there are still no weights, add 1.0 for the root bone
    if len(weights) == 0:
        weights[downcast(bpy.types.Armature, armatureObject.data).bones[0].name] = 1.0

    # the combined weight must be normalized to 1
    sum = 0
    for weight in weights.values():
        sum += weight

    for key in weights.keys():
        weights[key] /= sum

    return weights


class MdxmHeader:

    def __init__(self):
        self.name = ""
        self.animName = b""
        self.numBones: int = -1
        self.numLODs: int = -1
        self.ofsLODs: int = -1
        self.numSurfaces: int = -1
        self.ofsSurfHierarchy: int = -1
        self.ofsEnd: int = -1

    def loadFromFile(self, file: BinaryIO) -> Tuple[bool, ErrorMessage]:
        # ident check
        ident, = unpack_cast(Tuple[bytes], struct.unpack("4s", file.read(4)))
        if ident != JAG2Constants.GLM_IDENT:
            print("File does not start with ", JAG2Constants.GLM_IDENT,
                  " but ", ident, " - no GLM!")
            return False, ErrorMessage("Is no GLM file!")
        # version check
        version, = unpack_cast(Tuple[int], struct.unpack("i", file.read(4)))
        if version != JAG2Constants.GLM_VERSION:
            return False, ErrorMessage(f"Wrong glm file version! ({version} should be {JAG2Constants.GLM_VERSION})")
        # read data
        self.name, self.animName = unpack_cast(
            Tuple[bytes, bytes],
            struct.unpack("64s64s", file.read(JAG2Constants.MAX_QPATH * 2)))
        # 4x is 4 ignored bytes - the animIndex which is only used ingame
        self.numBones, self.numLODs, self.ofsLODs, self.numSurfaces, self.ofsSurfHierarchy, self.ofsEnd = unpack_cast(
            Tuple[int, int, int, int, int, int],
            struct.unpack("4x6i", file.read(4 * 7)))
        return True, NoError

    def saveToFile(self, file: BinaryIO) -> None:
        # 0 is animIndex, only used ingame
        file.write(struct.pack("4si64s64s7i", JAG2Constants.GLM_IDENT, JAG2Constants.GLM_VERSION, self.name, self.animName,
                   0, self.numBones, self.numLODs, self.ofsLODs, self.numSurfaces, self.ofsSurfHierarchy, self.ofsEnd))

    def print(self) -> None:
        print("== GLM Header ==\nname: {self.name}\nanimName: {self.animName}\nnumBones: {self.numBones}\nnumLODs: {self.numLODs}\nnumSurfaces: {self.numSurfaces}".format(
            self=self))

    @staticmethod
    def getSize() -> int:
        # 2 ints, 2 string, 7 ints
        return 2 * 4 + 2 * 64 + 7 * 4

# offsets of the surface data


class MdxmSurfaceDataOffsets:
    def __init__(self):
        self.baseOffset = MdxmHeader.getSize()  # always directly after the header
        self.offsets: List[int] = []

    def loadFromFile(self, file: BinaryIO, numSurfaces: int) -> None:
        assert (self.baseOffset == file.tell())
        for i in range(numSurfaces):
            self.offsets.append(struct.unpack("i", file.read(4))[0])

    def saveToFile(self, file: BinaryIO) -> None:
        for offset in self.offsets:
            file.write(struct.pack("i", offset))

    def calculateOffsets(self, surfaceDataCollection: "MdxmSurfaceDataCollection") -> None:
        offset = 4 * len(surfaceDataCollection.surfaces)
        for surfaceData in surfaceDataCollection.surfaces:
            self.offsets.append(offset)
            offset += surfaceData.getSize()

    # returns the size of this in bytes (when written to file)
    def getSize(self) -> int:
        return 4 * len(self.offsets)

# originally called mdxmSurfaceHierarchy_t, I think that name is misleading (but mine's not too good, either)


class MdxmSurfaceData:
    def __init__(self):
        self.name = b""
        self.flags = -1
        self.shader = b""
        self.parentIndex = -1
        self.numChildren = -1
        self.children: List[int] = []
        self.index = -1  # filled by MdxmSurfaceHierarchy.loadFromFile, not saved

    def loadFromFile(self, file: BinaryIO) -> None:
        self.name, self.flags, self.shader = unpack_cast(
            Tuple[bytes, int, bytes],
            struct.unpack(
                "64sI64s", file.read(64 + 4 + 64)))
        # ignoring shaderIndex which is only used ingame
        self.parentIndex, self.numChildren = unpack_cast(
            Tuple[int, int],
            struct.unpack(
                "4x2i", file.read(3 * 4)))
        for i in range(self.numChildren):
            self.children.append(struct.unpack("i", file.read(4))[0])

    def loadFromBlender(self, object: bpy.types.Object, surfaceIndexMap: Dict[str, int]) -> Tuple[bool, ErrorMessage]:
        self.name: bytes = getName(object).encode()
        self.shader: bytes = object.g2_prop_shader.encode()  # pyright: ignore [reportAttributeAccessIssue]
        # set flags
        self.flags = 0
        if object.g2_prop_off:  # pyright: ignore [reportAttributeAccessIssue]
            self.flags |= JAG2Constants.SURFACEFLAG_OFF
        if object.g2_prop_tag:  # pyright: ignore [reportAttributeAccessIssue]
            self.flags |= JAG2Constants.SURFACEFLAG_TAG
        # set parent
        if object.parent != None and getName(object.parent) in surfaceIndexMap:
            self.parentIndex = surfaceIndexMap[getName(object.parent)]
        # set children
        self.numChildren = 0
        for child in object.children:
            if child.type == 'MESH':  # working around non-mesh garbage in the hierarchy would be too much trouble, everything below that is ignored
                if not JAG2Panels.hasG2MeshProperties(child):
                    return False, ErrorMessage(f"{child.name} has no Ghoul 2 properties set!")
                childName = getName(child)
                if childName not in surfaceIndexMap:
                    surfaceIndexMap[childName] = len(surfaceIndexMap)
                self.children.append(surfaceIndexMap[childName])
                self.numChildren += 1
        return True, NoError

    def saveToFile(self, file: BinaryIO) -> None:
        # 0 is the shader index, only used ingame
        file.write(struct.pack("64sI64s3i", self.name, self.flags,
                   self.shader, 0, self.parentIndex, self.numChildren))
        for i in range(self.numChildren):
            file.write(struct.pack("i", self.children[i]))

    def getSize(self) -> int:
        # string, int, string, 4 ints
        return 64 + 4 + 64 + 3 * 4 + 4 * self.numChildren

# all the surface hierarchy/shader/name/flag/... information entries (MdxmSurfaceInfo)


class MdxmSurfaceDataCollection:
    def __init__(self):
        self.surfaces: List[MdxmSurfaceData] = []

    def loadFromFile(self, file: BinaryIO, surfaceInfoOffsets: MdxmSurfaceDataOffsets) -> None:
        for i, offset in enumerate(surfaceInfoOffsets.offsets):
            file.seek(surfaceInfoOffsets.baseOffset + offset)
            surfaceInfo = MdxmSurfaceData()
            surfaceInfo.loadFromFile(file)
            surfaceInfo.index = i
            self.surfaces.append(surfaceInfo)

    def loadFromBlender(self, rootObject: bpy.types.Object, surfaceIndexMap: Dict[str, int]) -> Tuple[bool, ErrorMessage]:
        visitedChildren: Dict[str, bpy.types.Object] = {}
        surfaces: List[Optional[MdxmSurfaceData]] = []

        def addChildren(object: bpy.types.Object) -> Tuple[bool, ErrorMessage]:
            for child in object.children:
                # only meshes supported in hierarchy, I couldn't always use the parent otherwise
                if child.type != 'MESH':
                    print(
                        f"Warning: {child.name} is no mesh, neither it nor its children will be exported!")
                elif not JAG2Panels.hasG2MeshProperties(child):
                    return False, ErrorMessage(f"{child.name} has no Ghoul 2 properties set! (Also, the exporter should've detected this earlier.)")
                else:
                    # assign the child an index, if it doesn't have one already
                    name = getName(child)
                    if (dupe := visitedChildren.get(name)) is not None:
                        return False, ErrorMessage(f"Objects \"{child.name}\" and \"{dupe.name}\" share G2 name \"{name}\"")
                    visitedChildren[name] = child

                    if (index := surfaceIndexMap.get(name)) is None:
                        index = len(surfaceIndexMap)
                        surfaceIndexMap[name] = index

                    # create the surface
                    surface = MdxmSurfaceData()
                    surface.index = index
                    success, message = surface.loadFromBlender(
                        child, surfaceIndexMap)
                    if not success:
                        return False, message

                    # extend the surface list to include the index, if necessary
                    if index >= len(self.surfaces):
                        surfaces.extend(
                            [None] * (index + 1 - len(surfaces)))
                    surfaces[index] = surface

                    success, message = addChildren(child)
                    if not success:
                        return False, message
            return True, NoError
        success, message = addChildren(rootObject)
        if not success:
            return False, message
        emptyIndices = [i for i, x in enumerate(surfaces) if x is None]
        if len(emptyIndices) > 0:  # a surface that was referenced did not get created
            return False, ErrorMessage(f"Internal error during hierarchy creation! (Surfaces {emptyIndices} referenced but not created)")
        self.surfaces = optional_list_cast(List[MdxmSurfaceData], surfaces)
        return True, NoError

    def saveToFile(self, file: BinaryIO) -> None:
        for surfaceInfo in self.surfaces:
            surfaceInfo.saveToFile(file)

    def getSize(self) -> int:
        size = 0
        for surface in self.surfaces:
            size += surface.getSize()
        return size


@dataclass
class ImportMetadata:
    gla: JAG2GLA.GLA
    scene_root: bpy.types.Object
    surfaceDataCollection: MdxmSurfaceDataCollection
    materialManager: JAMaterialmanager.MaterialManager
    boneNames: Dict[int, str]


class MdxmVertex:
    def __init__(self):
        self.co: List[float] = []
        self.normal: List[float] = []
        self.uv: List[float] = []
        self.numWeights = 1
        self.weights: List[float] = []
        self.boneIndices: List[int] = []

    # doesn't load UV since that comes later
    def loadFromFile(self, file):
        self.normal.extend(struct.unpack("3f", file.read(3 * 4)))
        self.co.extend(struct.unpack("3f", file.read(3 * 4)))
        # this is a packed structure that contains all kinds of things...
        packedStuff, = unpack_cast(
            Tuple[int],
            struct.unpack("I", file.read(4)))
        # this is not the complete weights, parts of it are in the packed stuff
        weights: List[int] = []
        weights.extend(struct.unpack("4B", file.read(4)))
        # packedStuff bits 31 & 30: weight count
        self.numWeights = (packedStuff >> 30) + 1
        # packedStuff bits 29 & 28: nothing
        # packedStuff bits 20f, 22f, 24f, 26f: weight overflow
        totalWeight = 0
        for i in range(self.numWeights):
            # add overflow bits to the weight (MSBs!)
            recomposed_weight = weights[i] | (
                ((packedStuff >> (20 + 2 * i)) & 0b11) << 8)
            # convert to float (0..1023 -> 0.0..1.0)
            normalized_weight = recomposed_weight / 1023
            if i + 1 < self.numWeights:
                totalWeight += normalized_weight
                self.weights.append(normalized_weight)
            else:  # i+1 == self.numWeights:
                self.weights.append(1 - totalWeight)
        # packedStuff 0-19: bone indices, 5 bit each
        for i in range(self.numWeights):
            self.boneIndices.append((packedStuff >> (5 * i)) & 0b11111)

    # index: this surface's index
    # does not save UV (comes later)
    def saveToFile(self, file: BinaryIO) -> None:
        assert (len(self.weights) == self.numWeights)
        #  pack the stuff that needs packing
        # num weights
        packedStuff = (self.numWeights - 1) << 30
        weights = [0, 0, 0, 0]
        for index, weight in enumerate(self.weights):
            # convert weight to 10 bit integer
            weight = round(weight * 1023)
            # lower 8 bits
            weights[index] = weight & 0xff
            # higher 2 bits
            hiWeight = (weight & 0x300) >> 8
            packedStuff |= hiWeight << (20 + 2 * index)
            # bone index - 5 bits
            boneIndex = (self.boneIndices[index]) & 0b11111
            packedStuff |= boneIndex << (5 * index)
        assert (packedStuff < 1 << 32)
        file.write(struct.pack("6fI4B", self.normal[0], self.normal[1], self.normal[2], self.co[0],
                   self.co[1], self.co[2], packedStuff, weights[0], weights[1], weights[2], weights[3]))

    # vertex :: Blender MeshVertex
    # uv :: [int, int] (blender style, will be y-flipped)
    # boneIndices :: { string -> int } (bone name -> index, may be changed)
    def loadFromBlender(self, vertex: bpy.types.MeshVertex, uv: List[float], normal: mathutils.Vector, boneIndices: Dict[str, int], meshObject: bpy.types.Object, armatureObject: Optional[bpy.types.Object]) -> Tuple[bool, ErrorMessage]:
        # I'm taking the world matrix in case the object is not at the origin, but I really want the coordinates in scene_root-space, so I'm using that, too.
        rootMat = matrix_getter_cast(bpy_generic_cast(bpy.types.Object, bpy.data.objects["scene_root"]).matrix_world).inverted()
        co = vector_overload_cast(rootMat @ vector_overload_cast(matrix_getter_cast(meshObject.matrix_world) @ vector_getter_cast(vertex.co)))
        normal = vector_overload_cast(rootMat.to_quaternion() @ vector_overload_cast(matrix_getter_cast(meshObject.matrix_world).to_quaternion() @ normal))
        for i in range(3):
            self.co.append(co[i])
            self.normal.append(normal[i])

        self.uv = [uv[0], 1 - uv[1]]  # flip Y

        # weight/bone indices

        assert (len(self.weights) == 0)
        if armatureObject == None:  # default skeleton
            self.weights.append(1.0)
            self.boneIndices.append(0)
            self.numWeights = 1
        else:
            weights = None
            try:
                weights = getBoneWeights(vertex, meshObject, armatureObject, 4)
            except GetBoneWeightException as e:
                return False, ErrorMessage(f"Could not retrieve vertex bone weights: {e}")
            self.numWeights = len(weights)
            for boneName, weight in weights.items():
                self.weights.append(weight)
                if boneName in boneIndices:
                    self.boneIndices.append(boneIndices[boneName])
                else:
                    index = len(boneIndices)
                    boneIndices[boneName] = index
                    self.boneIndices.append(index)
                    if len(boneIndices) > 32:
                        return False, ErrorMessage(f"More than 32 bones! ({len(boneIndices)})")

        assert (len(self.weights) == self.numWeights)

        return True, NoError


class MdxmTriangle:
    def __init__(self, indices: Optional[List[int]] = None):
        # order gets reversed during load/save
        self.indices = [] if indices is None else indices

    def loadFromFile(self, file: BinaryIO) -> None:
        self.indices.extend(struct.unpack("3i", file.read(3 * 4)))
        # flip CW/CCW
        self.indices[0], self.indices[2] = self.indices[2], self.indices[0]
        # make sure last index is not 0, eeekadoodle or something...
        if self.indices[2] == 0:
            self.indices[0], self.indices[1], self.indices[2] = self.indices[2], self.indices[0], self.indices[1]

    def saveToFile(self, file: BinaryIO) -> None:
        # triangles are flipped because otherwise they'd face the wrong way.
        file.write(struct.pack(
            "3i", self.indices[2], self.indices[1], self.indices[0]))

    # "for x in triangle" support
    def __getitem__(self, index: int) -> int:
        return self.indices[index]


class MdxmSurface:
    def __init__(self):
        self.index = -1
        self.numVerts = -1
        self.ofsVerts = -1
        self.numTriangles = -1
        self.ofsTriangles = -1
        self.numBoneReferences = -1
        self.ofsBoneReferences = -1
        self.ofsEnd = -1  # = size
        self.vertices: List[MdxmVertex] = []
        self.triangles: List[MdxmTriangle] = []
        # integers: bone indices. maximum of 32, thus can be stored in 5 bit in vertices, saves space.
        self.boneReferences: List[int] = []

    def loadFromFile(self, file) -> None:
        startPos = file.tell()
        #  load surface header
        # in the beginning I ignore the ident, which is usually 0 and shouldn't matter
        self.index, ofsHeader, self.numVerts, self.ofsVerts, self.numTriangles, self.ofsTriangles, self.numBoneReferences, self.ofsBoneReferences, self.ofsEnd = unpack_cast(
            Tuple[int, int, int, int, int, int, int, int, int],
            struct.unpack(
                "4x9i", file.read(10 * 4)))
        assert (ofsHeader == -startPos)

        #  load vertices
        file.seek(startPos + self.ofsVerts)
        for i in range(self.numVerts):
            vert = MdxmVertex()
            vert.loadFromFile(file)
            self.vertices.append(vert)

        # uv textures come later
        for vert in self.vertices:
            vert.uv.extend(struct.unpack("2f", file.read(2 * 4)))

        #  load triangles
        file.seek(startPos + self.ofsTriangles)
        for i in range(self.numTriangles):
            t = MdxmTriangle()
            t.loadFromFile(file)
            self.triangles.append(t)

        #  load bone references
        file.seek(startPos + self.ofsBoneReferences)
        assert (len(self.boneReferences) == 0)
        self.boneReferences.extend(struct.unpack(
            str(self.numBoneReferences) + "i", file.read(4 * self.numBoneReferences)))

        print(
            f"surface {self.index}: numBoneReferences: {self.numBoneReferences}")
        for i, boneRef in enumerate(self.boneReferences):
            print(f"bone ref {i}: {boneRef}")

        if file.tell() != startPos + self.ofsEnd:
            print(
                "Warning: Surface structure unordered (bone references not last) or read error")
            file.seek(startPos + self.ofsEnd)

    def loadFromBlender(self, object: bpy.types.Object, surfaceData: MdxmSurfaceData, boneIndexMap: Optional[BoneIndexMap], armatureObject: Optional[bpy.types.Object]) -> Tuple[bool, ErrorMessage]:
        if object.type != 'MESH':
            return False, ErrorMessage(f"Object {object.name} is not of type Mesh!")
        mesh: bpy.types.Mesh = downcast(bpy.types.Object, object.evaluated_get(
            bpy.context.evaluated_depsgraph_get())).to_mesh()

        boneIndices: Dict[str, int] = {}

        # This is a tag, use a simpler export procedure
        if surfaceData.flags & JAG2Constants.SURFACEFLAG_TAG:
            print(f"{object.name} is a tag")
            for face in mesh.polygons:
                if len(face.vertices) != 3:
                    return False, ErrorMessage(f"Non-triangle tag found: {object.name}!")
            for vi in mesh.vertices:
                vi = bpy_generic_cast(bpy.types.MeshVertex, vi)
                vert = MdxmVertex()
                success, message = vert.loadFromBlender(
                    vi, [0, 0], mathutils.Vector(), boneIndices, object, armatureObject)
                if not success:
                    return False, ErrorMessage(f"Mesh {mesh.name} has invalid vertex: {message}")
                self.vertices.append(vert)
            self.triangles = [MdxmTriangle(
                [face.vertices[0], face.vertices[1], face.vertices[2]]) for face in mesh.polygons]

            self.numVerts = len(mesh.vertices)
            self.numTriangles = len(mesh.polygons)

        # This is not a tag, do normal things
        else:

            uv_layer = mesh.uv_layers.active.data
            if not uv_layer:
                return False, ErrorMessage("No UV coordinates found!")

            protoverts = []

            for face in mesh.polygons:
                triangle = []
                if len(face.vertices) != 3:
                    return False, ErrorMessage("Non-triangle face found!")
                for i in range(3):
                    loop = bpy_generic_cast(bpy.types.MeshLoop, mesh.loops[face.loop_start + i])
                    v = loop.vertex_index
                    u = uv_layer[loop.index].uv
                    n = vector_getter_cast(loop.normal if mesh.has_custom_normals else bpy_generic_cast(bpy.types.MeshVertex, mesh.vertices[loop.vertex_index]).normal)

                    proto_found = -1
                    for j in range(len(protoverts)):
                        proto = protoverts[j]
                        if proto[0] == v and proto[1] == u and abs(proto[2][0] - n[0]) < 0.05 and abs(proto[2][1] - n[1]) < 0.05 and abs(proto[2][2] - n[2]) < 0.05:
                            proto_found = j
                            break

                    if proto_found >= 0:
                        triangle.append(proto_found)
                    else:
                        vertex = MdxmVertex()
                        success, message = vertex.loadFromBlender(
                            mesh.vertices[v], u, n, boneIndices, object, armatureObject)
                        if not success:
                            return False, ErrorMessage(f"Surface has invalid vertex: {message}")
                        protoverts.append((v, u, n))
                        self.vertices.append(vertex)
                        triangle.append(len(protoverts) - 1)
                self.triangles.append(MdxmTriangle(triangle))

            self.numVerts = len(protoverts)
            self.numTriangles = len(mesh.polygons)

            if self.numVerts > 1000:
                print(f"Warning: {object.name} has over 1000 vertices ({self.numVerts})")

        assert (len(self.vertices) == self.numVerts)
        assert (len(self.triangles) == self.numTriangles)

        # fill bone references
        if boneIndexMap is None:  # default skeleton
            self.boneReferences = [0]
        else:
            boneReferences: List[Optional[int]] = [None] * len(boneIndices)
            for boneName, index in boneIndices.items():
                boneReferences[index] = boneIndexMap[boneName]
            missingIndices = [i for i, x in enumerate(boneReferences) if x is None]
            if len(missingIndices) > 0:
                return False, ErrorMessage(f"bug: boneIndexMap did not fill indices {missingIndices}")

            self.boneReferences = optional_list_cast(List[int], boneReferences)

        self._calculateOffsets()
        return True, NoError

    # if a surface does not exist on a lower LOD, an empty one gets created
    def makeEmpty(self):
        self.numVerts = 0
        self.numTriangles = 0
        self.numBoneReferences = 0
        self._calculateOffsets()

    def saveToFile(self, file):
        startPos = file.tell()
        #  write header (= this)
        # 0 = ident
        file.write(struct.pack("10i", 0, self.index, -startPos, self.numVerts, self.ofsVerts,
                   self.numTriangles, self.ofsTriangles, self.numBoneReferences, self.ofsBoneReferences, self.ofsEnd))

        # I don't know if triangles *have* to come first, but when I export they do, hence the assertions.

        #  write triangles
        assert (file.tell() == startPos + self.ofsTriangles)
        for tri in self.triangles:
            tri.saveToFile(file)

        #  write vertices
        assert (file.tell() == startPos + self.ofsVerts)
        # write packed part
        for vert in self.vertices:
            vert.saveToFile(file)
        # write UVs
        for vert in self.vertices:
            file.write(struct.pack("2f", vert.uv[0], vert.uv[1]))

        #  write bone indices
        assert (file.tell() == startPos + self.ofsBoneReferences)
        for ref in self.boneReferences:
            file.write(struct.pack("i", ref))

        assert (file.tell() == startPos + self.ofsEnd)

    # returns the created object
    def saveToBlender(self, data: ImportMetadata, lodLevel: int):
        #  retrieve metadata (same across LODs)
        surfaceData = data.surfaceDataCollection.surfaces[self.index]
        # blender won't let us create multiple things with the same name, so we add a LOD-suffix
        name = JAStringhelper.decode(surfaceData.name)
        blenderName = name + "_" + str(lodLevel)

        #  create mesh
        mesh = bpy.data.meshes.new(blenderName)
        mesh.from_pydata([v.co for v in self.vertices], [], [
                         triangle.indices for triangle in self.triangles])

        material = data.materialManager.getMaterial(name, surfaceData.shader)
        if material == None:
            material = bpy.data.materials.new(
                name=JAStringhelper.decode(surfaceData.shader))
        mesh.materials.append(material)

        # this is probably actually bullshit, since vertex order is what determines a tag, not index order! I think.
        """
		# if this is a tag, changing the index order is not such a good idea. So let's change the vertex order, too!
		if len( self.vertices ) == 3 and len( self.triangles ) == 1 and self.triangles[0].indices[2] == 0:
			indexmap = { 0 : 2, 1 : 0, 2 : 1 }
			self.vertices = [ self.vertices[ indexmap[ i ] ] for i in range( 3 ) ]
			self.triangles[0].indices = [ indexmap[ self.triangles[0][ i ] ] for i in range( 3 ) ]
		"""

        mesh.validate()

        mesh.normals_split_custom_set_from_vertices(
            [v.normal for v in self.vertices])

        uv_layer = mesh.uv_layers.new()
        uv_loops = uv_layer.data
        for poly in mesh.polygons:
            indices = [mesh.loops[poly.loop_start +
                                  i].vertex_index for i in range(3)]
            uvs = [[self.vertices[index].uv[0], 1 - self.vertices[index].uv[1]]
                   for index in indices]
            for i, uv in enumerate(uvs):
                uv_loops[poly.loop_start + i].uv = uv

        mesh.update()

        #  create object
        obj = bpy.data.objects.new(blenderName, mesh)

        # in the case of the default skeleton, no weighting is needed.
        if not data.gla.isDefault:

            #  create armature modifier
            armatureModifier = downcast(bpy.types.ArmatureModifier, obj.modifiers.new("armature", 'ARMATURE'))
            armatureModifier.object = optional_cast(bpy.types.Object, data.gla.skeleton_object)
            armatureModifier.use_bone_envelopes = False  # only use vertex groups by default

            #  create vertex groups (indices will match)
            for index in self.boneReferences:
                if index not in data.boneNames:
                    raise Exception(
                        "Bone Index {} not in LookupTable!".format(index))
                obj.vertex_groups.new(name=data.boneNames[index])

            # set weights
            for vertIndex, vert in enumerate(self.vertices):
                for weightIndex in range(vert.numWeights):
                    obj.vertex_groups[vert.boneIndices[weightIndex]].add(
                        [vertIndex], vert.weights[weightIndex], 'ADD')

        # link object to scene
        bpy.context.scene.collection.objects.link(obj)

        # make object active - needed for this smoothing operator and possibly for material adding later
        bpy.context.view_layer.objects.active = obj

        # set ghoul2 specific properties
        obj.g2_prop_name = name  # pyright: ignore [reportAttributeAccessIssue]
        obj.g2_prop_shader = surfaceData.shader.decode()  # pyright: ignore [reportAttributeAccessIssue]
        obj.g2_prop_tag = not not (surfaceData.flags & JAG2Constants.SURFACEFLAG_TAG)  # pyright: ignore [reportAttributeAccessIssue]
        obj.g2_prop_off = not not (surfaceData.flags & JAG2Constants.SURFACEFLAG_OFF)  # pyright: ignore [reportAttributeAccessIssue]

        # return object so hierarchy etc. can be set
        return obj

    # fill offset and number variables
    def _calculateOffsets(self):
        offset = 10 * 4  # header: 4 ints
        # triangles
        self.ofsTriangles = offset
        self.numTriangles = len(self.triangles)
        offset += 3 * 4 * self.numTriangles  # 3 ints
        # vertices
        self.ofsVerts = offset
        self.numVerts = len(self.vertices)
        offset += 10 * 4 * self.numVerts  # 6 floats co/normal, 8 bytes packed, 2 floats UV
        # bone references
        self.ofsBoneReferences = offset
        self.numBoneReferences = len(self.boneReferences)
        offset += 4 * self.numBoneReferences  # 1 int each
        # that's all the content, so we've got total size now.
        self.ofsEnd = offset


class MdxmLOD:
    def __init__(self, surfaceOffsets: List[int], level: int, surfaces: List[MdxmSurface], ofsEnd: int):
        self.surfaceOffsets = surfaceOffsets
        self.level = level
        self.surfaces = surfaces
        self.ofsEnd = ofsEnd  # = size

    @staticmethod
    def loadFromFile(file: BinaryIO, level: int, header: MdxmHeader) -> "MdxmLOD":
        startPos = file.tell()
        ofsEnd, = unpack_cast(Tuple[int], struct.unpack("i", file.read(4)))
        # surface offsets - they're relative to a structure after the one containing ofsEnd, so I need to add sizeof(int) to them later.
        surfaceOffsets = unpack_cast(List[int], list(struct.unpack(f"{header.numSurfaces}i", file.read(4 * header.numSurfaces))))
        surfaces: List[MdxmSurface] = []
        for surfaceIndex, offset in enumerate(surfaceOffsets):
            if file.tell() != startPos + 4 + offset:
                print("Warning: Surface not completely read or unordered")
                file.seek(startPos + offset + 4)
            surface = MdxmSurface()
            surface.loadFromFile(file)
            assert (surface.index == surfaceIndex)
            surfaces.append(surface)
        assert (file.tell() == startPos + ofsEnd)
        return MdxmLOD(
            surfaceOffsets=surfaceOffsets,
            level=level,
            surfaces=surfaces,
            ofsEnd=ofsEnd,
        )

    def saveToFile(self, file: BinaryIO) -> None:
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
        assert (file.tell() == startPos + self.ofsEnd)

    @staticmethod
    def loadFromBlender(level: int, model_root: bpy.types.Object, surfaceIndexMap: Dict[str, int], surfaceDataCollection: MdxmSurfaceDataCollection, boneIndexMap: Optional[BoneIndexMap], armatureObject: Optional[bpy.types.Object]) -> Tuple[Optional["MdxmLOD"], ErrorMessage]:
        # self.level gets set by caller

        # create dictionary of available objects
        def addChildren(dict, object):
            for child in object.children:
                if child.type == 'MESH' and JAG2Panels.hasG2MeshProperties(child):
                    dict[getName(child)] = child
                addChildren(dict, child)
        available = {}
        addChildren(available, model_root)

        surfaces: List[Optional[MdxmSurface]] = [None] * len(surfaceIndexMap)
        # for each required surface:
        for name, index in surfaceIndexMap.items():
            # create surface
            surf = MdxmSurface()
            # set correct index
            surf.index = index
            # if it is available:
            if name in available:
                surfaceData = surfaceDataCollection.surfaces[index]
                # load from blender
                success, message = surf.loadFromBlender(
                    available[name], surfaceData, boneIndexMap, armatureObject)
                if not success:
                    return None, ErrorMessage(f"could not load surface {name}: {message}")
            # not available?
            else:
                # create empty one
                surf.makeEmpty()
            # add surface to list
            surfaces[index] = surf
        missingIndices = [i for i, x in enumerate(surfaces) if x is None]
        if len(missingIndices) > 0:
            return None, ErrorMessage(f"internal error: surface index map has missing indices {missingIndices}")
        return MdxmLOD(
            surfaceOffsets=[],  # FIXME: avoid this invalid state
            level=level,
            surfaces=optional_list_cast(List[MdxmSurface], surfaces),
            ofsEnd=-1,  # FIXME: avoid this invalid state
        ), NoError

    def saveToBlender(self, data: ImportMetadata, root: bpy.types.Object):
        # 1st pass: create objects
        objects = []
        for surface in self.surfaces:
            if surface is not None:
                obj = surface.saveToBlender(data, self.level)
                objects.append(obj)
        # 2nd pass: set parent relations
        for i, obj in enumerate(objects):
            parentIndex = data.surfaceDataCollection.surfaces[i].parentIndex
            parent = root
            if parentIndex != -1:
                parent = objects[parentIndex]
            obj.parent = parent

    # fills self.surfaceOffsets and self.ofsEnd based on self.surfaces (must be initialized)
    def calculateOffsets(self, myOffset):
        self.surfaceOffsets = []
        # ofsEnd is in front of offsets, but they are relative to their start
        offset = 4 * len(self.surfaces)
        for surface in self.surfaces:
            self.surfaceOffsets.append(offset)
            offset += surface.ofsEnd  # = size
        # memory required for ofsEnd
        self.ofsEnd = offset + 4

    def getSize(self):
        # ofsEnd + surface offsets
        size = 4 + 4 * len(self.surfaces)
        for surface in self.surfaces:
            size += surface.ofsEnd
        return size


class MdxmLODCollection:
    def __init__(self):
        self.LODs: List[MdxmLOD] = []

    def loadFromFile(self, file: BinaryIO, header: MdxmHeader) -> None:
        for i in range(header.numLODs):
            startPos = file.tell()
            curLOD = MdxmLOD.loadFromFile(file, i, header)
            if file.tell() != startPos + curLOD.ofsEnd:
                print("Warning: Internal reading error or LODs not tightly packed!")
                file.seek(startPos + curLOD.ofsEnd)
            self.LODs.append(curLOD)

    def loadFromBlender(self, rootObjects: List[bpy.types.Object], surfaceIndexMap: Dict[str, int], surfaceDataCollection: MdxmSurfaceDataCollection, boneIndexMap: Optional[BoneIndexMap], armatureObject: Optional[bpy.types.Object]) -> Tuple[bool, ErrorMessage]:
        for lodLevel, model_root in enumerate(rootObjects):
            lod, message = MdxmLOD.loadFromBlender(
                lodLevel, model_root, surfaceIndexMap, surfaceDataCollection, boneIndexMap, armatureObject)
            if lod is None:
                return False, ErrorMessage(f"loading LOD {lodLevel} from Blender: {message}")
            self.LODs.append(lod)
        return True, NoError

    def calculateOffsets(self, ofsLODs):
        offset = ofsLODs
        for lod in self.LODs:
            lod.calculateOffsets(offset)
            offset += lod.getSize()

    def saveToFile(self, file: BinaryIO) -> None:
        for LOD in self.LODs:
            LOD.saveToFile(file)

    def saveToBlender(self, data: ImportMetadata):
        for i, LOD in enumerate(self.LODs):
            root = bpy.data.objects.new("model_root_" + str(i), None)
            root.parent = data.scene_root
            bpy.context.scene.collection.objects.link(root)
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

    def loadFromFile(self, filepath_abs: str) -> Tuple[bool, ErrorMessage]:
        print(f"Loading {filepath_abs}...")
        profiler = MrwProfiler.SimpleProfiler(True)
        # open file
        try:
            file = open(filepath_abs, mode="rb")
        except IOError as e:
            print(f"Could not open file: {filepath_abs}")
            return False, ErrorMessage(f"Could not open file: {e}")
        profiler.start("reading header")
        success, message = self.header.loadFromFile(file)
        if not success:
            return False, message
        profiler.stop("reading header")

        # self.header.print()

        # load surface hierarchy offsets
        profiler.start("reading surface hierarchy")
        self.surfaceDataOffsets.loadFromFile(file, self.header.numSurfaces)

        # load surfaces' information - seeks positon using surfaceDataOffsets
        self.surfaceDataCollection.loadFromFile(file, self.surfaceDataOffsets)
        profiler.stop("reading surface hierarchy")

        # load LODs
        profiler.start("reading surfaces")
        file.seek(self.header.ofsLODs)
        self.LODCollection.loadFromFile(file, self.header)
        profiler.stop("reading surfaces")

        # should be at the end now, if the structures are in the expected order.
        if file.tell() != self.header.ofsEnd:
            print("Warning: File not completely read or LODs not last structure in file. The former would be a problem, the latter wouldn't.")
        return True, NoError

    def loadFromBlender(self, glm_filepath_rel: str, gla_filepath_rel: str, basepath: str) -> Tuple[bool, ErrorMessage]:
        self.header.name = glm_filepath_rel.replace("\\", "/").encode()
        self.header.animName = gla_filepath_rel.encode()
        # create BoneName->BoneIndex lookup table based on GLA file (keeping in mind it might be "*default"/"")
        defaultSkeleton: bool = (gla_filepath_rel ==
                                 "" or gla_filepath_rel == "*default")
        skeleton_object: Optional[bpy.types.Object] = None
        boneIndexMap: Optional[BoneIndexMap] = None
        if defaultSkeleton:
            # no skeleton available, generate default/unit skeleton instead
            self.header.numBones = 1
            self.header.animName = b"*default"
        else:
            # retrieve skeleton
            if not "skeleton_root" in bpy.data.objects:
                return False, ErrorMessage("No skeleton_root Object found!")
            obj = cast(bpy.types.Object, bpy.data.objects["skeleton_root"])
            skeleton_object = obj
            if obj.type != 'ARMATURE':
                return False, ErrorMessage("skeleton_root is no Armature!")
            skeleton_armature = downcast(bpy.types.Armature, obj.data)

            boneIndexMap, message = buildBoneIndexLookupMap(JAFilesystem.RemoveExtension(
                JAFilesystem.AbsPath(gla_filepath_rel, basepath)) + ".gla")
            if boneIndexMap is None:
                return False, message

            self.header.numBones = len(boneIndexMap)

            # check if skeleton matches the specified one
            for bone in skeleton_armature.bones:
                if bone.name not in boneIndexMap:
                    return False, ErrorMessage(f"skeleton_root does not match specified gla, could not find bone {bone.name}")

        #   load from Blender

        # find all available LODs
        self.header.numLODs = 0
        rootObjects: List[bpy.types.Object] = []
        while f"model_root_{self.header.numLODs}" in bpy.data.objects:
            rootObjects.append(
                bpy.data.objects[f"model_root_{self.header.numLODs}"])
            self.header.numLODs += 1
        print(
            f"Found {self.header.numLODs} model_root objects, i.e. LOD levels")

        if self.header.numLODs == 0:
            return False, ErrorMessage("Could not find model_root_0 object")

        # build hierarchy from first LOD
        surfaceIndexMap: Dict[str, int] = {}  # surface name -> index
        success, message = self.surfaceDataCollection.loadFromBlender(
            rootObjects[0], surfaceIndexMap)
        if not success:
            return False, message
        self.surfaceDataOffsets.calculateOffsets(self.surfaceDataCollection)

        self.header.numSurfaces = len(self.surfaceDataCollection.surfaces)
        print(f"{self.header.numSurfaces} surfaces found")

        # load all LODs
        success, message = self.LODCollection.loadFromBlender(
            rootObjects, surfaceIndexMap, self.surfaceDataCollection, boneIndexMap, skeleton_object)
        if not success:
            return False, message

        self.LODCollection.calculateOffsets(self.header.ofsLODs)

        #   calculate offsets etc.4
        self._calculateHeaderOffsets()
        return True, NoError

    def saveToFile(self, filepath_abs: str) -> Tuple[bool, ErrorMessage]:
        if JAFilesystem.FileExists(filepath_abs):
            print("Warning: File exists! Overwriting.")
        # open file
        try:
            file = open(filepath_abs, "wb")
        except IOError:
            print("Failed to open file for writing: ", filepath_abs, sep="")
            return False, ErrorMessage("Could not open file!")
        # save header
        self.header.saveToFile(file)
        # save surface data offsets
        self.surfaceDataOffsets.saveToFile(file)
        # save surface ("hierarchy") data
        self.surfaceDataCollection.saveToFile(file)
        # save LODs to file
        self.LODCollection.saveToFile(file)
        return True, NoError

    # calculates the offsets & counts saved in the header based on the rest
    def _calculateHeaderOffsets(self):
        # offset of "after header"
        baseOffset = MdxmHeader.getSize()
        # offset of "after hierarchy offset list"
        self.header.numSurfaces = len(self.surfaceDataOffsets.offsets)
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
    # gla: JAG2GLA.GLA object - the Skeleton (for weighting purposes)
    # scene_root: "scene_root" object in Blender
    def saveToBlender(self, basepath: str, gla: JAG2GLA.GLA, scene_root: bpy.types.Object, skin_rel: str, guessTextures: bool) -> Tuple[bool, ErrorMessage]:
        if gla.header.numBones != self.header.numBones:
            return False, ErrorMessage(f"Bone number mismatch - gla has {gla.header.numBones} bones, model uses {self.header.numBones}. Maybe you're trying to load a jk2 model with the jk3 skeleton or vice-versa?")
        print("creating model...")
        profiler = MrwProfiler.SimpleProfiler(True)
        profiler.start("creating surfaces")

        data = ImportMetadata(
            gla=gla,
            scene_root=scene_root,
            surfaceDataCollection=self.surfaceDataCollection,
            materialManager=JAMaterialmanager.MaterialManager(),
            boneNames={bone.index: bone.name for bone in gla.skeleton.bones}
        )
        success, message = data.materialManager.init(
            basepath, skin_rel, guessTextures)
        if not success:
            return False, message

        self.LODCollection.saveToBlender(data)
        profiler.stop("creating surfaces")
        return True, NoError

    def getRequestedGLA(self) -> str:
        # todo
        return JAStringhelper.decode(self.header.animName)
