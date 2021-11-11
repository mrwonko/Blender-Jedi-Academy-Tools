# python imports
import math
import struct
import os

# blender imports
import bpy
import mathutils


# Patch format - the patch looks like this, where P is a normal point, C is a control point:
#
# p2 c1 p1
# c2 c5 c4
# p3 c3 p4
#
# double braces due to str.format()
patchFormat = """{{
patchDef2
{{
{shader}
( 3 3 0 0 0 )
(
( ( {p2[0]:.3f} {p2[1]:.3f} {p2[2]:.3f} 0 0 ) ( {c1[0]:.3f} {c1[1]:.3f} {c1[2]:.3f} 0 0 ) ( {p1[0]:.3f} {p1[1]:.3f} {p1[2]:.3f} 0 0 ) )
( ( {c2[0]:.3f} {c2[1]:.3f} {c2[2]:.3f} 0 0 ) ( {c5[0]:.3f} {c5[1]:.3f} {c5[2]:.3f} 0 0 ) ( {c4[0]:.3f} {c4[1]:.3f} {c4[2]:.3f} 0 0 ) )
( ( {p3[0]:.3f} {p3[1]:.3f} {p3[2]:.3f} 0 0 ) ( {c3[0]:.3f} {c3[1]:.3f} {c3[2]:.3f} 0 0 ) ( {p4[0]:.3f} {p4[1]:.3f} {p4[2]:.3f} 0 0 ) )
)
}}
}}
"""

def mean2(p1, p2):
    return [ ( x[0] + x[1] ) / 2 for x in zip(p1, p2) ]
    
def mean4(p1, p2, p3, p4):
    return mean2( mean2( p1, p2 ), mean2( p3, p4 ) )


# Converts 3 or 4 vertice coordinates as [x, y, z] to a Patch Definition as in a .map file
def coordinatesToPatchDef(shader, p1, p2, p3, p4=None):
    # Triangle?
    if not p4:
        p4 = p3
    return patchFormat.format(
        shader=shader,
        # vertices
        p1=p1,
        p2=p2,
        p3=p3, 
        p4=p4,
        # control points
        c1=mean2(p1, p2),
        c2=mean2(p2, p3),
        c3=mean2(p3, p4),
        c4=mean2(p4, p1),
        c5=mean4(p1, p2, p3, p4)
        )

# same as above, but they're not nicely distributed
def coordinatesToPatchDefAlt(shader, p1, p2, p3, p4=None):
    # Triangle?
    if not p4:
        p4 = p3
    return patchFormat.format(
        shader=shader,
        # vertices
        p1=p1,
        p2=p2,
        p3=p3, 
        p4=p4,
        # control points
        c1=p1,
        c2=p3,
        c3=p4,
        c4=p4,
        c5=p4
        )

### The new operator ###
class patchmesh_export_operator(bpy.types.Operator):
    #everything is scaled down by this factor
    bl_idname = "export_scene.patchmesh_map"
    bl_label = "Export Patch Mesh (.map)"
    
    #gets set by the file select window - IBM (Internal Blender Magic) or whatever.
    filepath = bpy.props.StringProperty(name="File Path", description="File path used for the .map file", maxlen= 1024, default="")
    scale = bpy.props.FloatProperty(name="Scale", description="Factor by which to scale the object up", min=1, default=1)
    shader = bpy.props.StringProperty(name="Shader", description="Shader to put on the patches", maxlen=64, default="system/physics_clip")
    beautiful = bpy.props.BoolProperty(name="Even distribution", description="Whether to evenly distribute the patch handles (if disabled, they'll be at the corners)", default=True)
    
    def execute(self, context):
        self.ExportStart(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        windowMan = context.window_manager
        #sets self.properties.filename and runs self.execute()
        windowMan.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def ExportStart(self, context):
        filename = self.properties.filepath
        
        if os.path.exists(filename):
            #TODO: Overwrite yes/no
            pass
        
        
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')
        
        obj = bpy.context.active_object
        if not obj:
            self.report({"ERROR"}, "No active object!")
            return
        
        if obj.type != 'MESH':
            self.report({"ERROR"}, "Active object is no mesh!")
            return
        
        scaleMat = mathutils.Matrix.Scale(self.scale, 4)
        
        # if there are any non-quads/tris (n-gons), so we can warn in the end.
        ngons = False
        patchDefFunc = coordinatesToPatchDef
        if not self.beautiful:
            patchDefFunc = coordinatesToPatchDefAlt
        
        mesh = obj.to_mesh(bpy.context.scene,True,'PREVIEW')
        try:
            try:
                file = open(filename, "w")
                
                file.write("{\n\"classname\" \"worldspawn\"\n")
                
                for face in mesh.tessfaces:
                    if len(face.vertices) in (3, 4):
                        coordinates = [scaleMat * obj.matrix_world * mesh.vertices[x].co for x in face.vertices]
                        file.write( patchDefFunc( self.shader, *coordinates ) )
                    else:
                        ngons = True
                
                file.write("}\n")
                
                file.close()
            except IOError:
                self.report({"ERROR"}, "Couldn't create file!")
                return
        finally:
            bpy.data.meshes.remove(mesh)
        
        if ngons:
            self.report({'WARNING'}, "Some N-Gons could not be exported!")
            return

class Operator( bpy.types.Operator ):
    bl_idname = "export_scene.ja_patchmesh_map"
    bl_label = "Export JA Patch Mesh (.map)"
    
    #gets set by the file select window - IBM (Internal Blender Magic) or whatever.
    filepath = bpy.props.StringProperty(name="File Path", description="File path used for the .map file", maxlen= 1024, default="")
    scale = bpy.props.FloatProperty(name="Scale", description="Factor by which to scale the object up", min=1, default=1)
    shader = bpy.props.StringProperty(name="Shader", description="Shader to put on the patches", maxlen=64, default="system/physics_clip")
    beautiful = bpy.props.BoolProperty(name="Even distribution", description="Whether to evenly distribute the patch handles (if disabled, they'll be at the corners)", default=True)
    
    def execute(self, context):
        self.ExportStart(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        windowMan = context.window_manager
        #sets self.properties.filename and runs self.execute()
        windowMan.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def ExportStart(self, context):
        filename = self.properties.filepath
        
        if os.path.exists(filename):
            #TODO: Overwrite yes/no
            pass
        
        
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')
        
        obj = bpy.context.active_object
        if not obj:
            self.report({"ERROR"}, "No active object!")
            return
        
        if obj.type != 'MESH':
            self.report({"ERROR"}, "Active object is no mesh!")
            return
        
        scaleMat = mathutils.Matrix.Scale(self.scale, 4)
        
        # if there are any non-quads/tris (n-gons), so we can warn in the end.
        ngons = False
        patchDefFunc = coordinatesToPatchDef
        if not self.beautiful:
            patchDefFunc = coordinatesToPatchDefAlt
        
        mesh = obj.to_mesh(bpy.context.scene,True,'PREVIEW')
        try:
            try:
                file = open(filename, "w")
                
                file.write("{\n\"classname\" \"worldspawn\"\n")
                
                for face in mesh.tessfaces:
                    if len(face.vertices) in (3, 4):
                        coordinates = [scaleMat * obj.matrix_world * mesh.vertices[x].co for x in face.vertices]
                        file.write( patchDefFunc( self.shader, *coordinates ) )
                    else:
                        ngons = True
                
                file.write("}\n")
                
                file.close()
            except IOError:
                self.report({"ERROR"}, "Couldn't create file!")
                return
        finally:
            bpy.data.meshes.remove(mesh)
        
        if ngons:
            self.report({'WARNING'}, "Some N-Gons could not be exported!")
            return

def menu_func(self, context):
    self.layout.operator(Operator.bl_idname, text="JA Patchmesh (.map)")