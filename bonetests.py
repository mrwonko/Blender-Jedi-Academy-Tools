import bpy, mathutils, math

# take current object's matrix (that's kind of like having a basePoseMat)

# creates meshes representing the axes of this matrix
def displayMatrix(name, mat, alt=False):
    assert(type(name) == type(""))
    def createAxisObject(axisIndex, name):
        if alt:
            axis = [mat[0][axisIndex], mat[1][axisIndex], mat[2][axisIndex]]
        else:
            axis = [mat[axisIndex][0], mat[axisIndex][1], mat[axisIndex][2]]
        mesh = bpy.data.meshes.new(name)
        # vertices, lines, triangles
        mesh.from_pydata([[0, 0, 0], axis], [[0, 1]], [])
        obj = bpy.data.objects.new(name, mesh)
        obj.location = [mat[3][0], mat[3][1], mat[3][2]]
        bpy.context.scene.objects.link(obj)
    createAxisObject(0, name+"_x")
    createAxisObject(1, name+"_y")
    createAxisObject(2, name+"_z")

def visualizeEditBone(bone):
    def createAxisObject(direction, name):
        axis = []
        axis.extend(direction)
        while len(axis) > 3:
            del axis[3]
        mesh = bpy.data.meshes.new(name)
        # vertices, lines, triangles
        mesh.from_pydata([[0, 0, 0], axis], [[0, 1]], [])
        obj = bpy.data.objects.new(name, mesh)
        obj.location = bone.head
        bpy.context.scene.objects.link(obj)
    createAxisObject(bone.x_axis, bone.name+"_x")
    createAxisObject(bone.y_axis, bone.name+"_y")
    createAxisObject(bone.z_axis, bone.name+"_z")

#basePoseMat = bpy.context.object.matrix_world
#displayMatrix(bpy.context.object.name, basePoseMat)

# bone: Bone, *not* EditBone
# note: does not work as excepted.
def getBoneRoll(bone):
    mat = bone.matrix
    euler = mat.to_euler()
    return euler.z

visualizeEditBone(bpy.data.armatures['Armature'].edit_bones['Bone'])
return

mat = bpy.data.armatures['Armature'].bones['Bone'].matrix_local.copy()
mat.to_4x4()
loc = []
loc.extend(bpy.data.objects['Armature'].location)
assert(len(loc) == 3)
loc.append(1)
loc = mathutils.Vector(loc)
loc += mathutils.Vector(mat[3][:])
loc[3] = 1
mat[3] = loc

#note: there is EditBone.[xyz]_axis - lovely!
#note: I may be a friggin idiot. There is EditBone.align_roll(axis), which rolls the bone so Z points towards axis

# mat is now the exact matrix of this bone, if the armature isn't rotated/scale.
#displayMatrix("bone", mat)
possibleOrders = ['XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX']
for order in possibleOrders:
    euler = mat.to_euler(order)
    print(order, ".x: ", math.degrees(euler.x), " degrees", sep="")
    print(order, ".y: ", math.degrees(euler.y), " degrees", sep="")
    print(order, ".z: ", math.degrees(euler.z), " degrees", sep="", end="\n\n")