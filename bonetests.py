import bpy, mathutils

# take current object's matrix (that's kind of like having a basePoseMat)

basePoseMat = bpy.context.object.matrix_world

# creates meshes representing the axes of this matrix
def displayMatrix(name, mat):
    assert(type(name) == type(""))
    def createAxisObject(axisIndex, name):
        #axis = [mat[0][axisIndex], mat[1][axisIndex], mat[2][axisIndex]]
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

displayMatrix(bpy.context.object.name, basePoseMat)