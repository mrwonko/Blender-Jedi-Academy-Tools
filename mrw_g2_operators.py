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

import bpy

class GLMImport(bpy.types.Operator):
        '''Import GLM Operator.'''
        bl_idname = "import_scene.glm"
        bl_label = "Import Ghoul 2 Model (.glm)"
        bl_description = "Imports a Ghoul 2 model (.glm), looking up the skeleton (and optionally the animation) from the referenced (or optionally a different) .gla file."
        bl_options = {'REGISTER', 'UNDO'}

        filepath = bpy.props.StringProperty(name="File Path", description="The .glm file to import", maxlen=1024, default="")

        def execute(self, context):
            #from . import 
            print("Import:", self.filepath)
            #todo
            #    self.report({'ERROR'}, message)
            return {'FINISHED'}

        def invoke(self, context, event):
            wm= context.window_manager
            wm.fileselect_add(self)
            return {'RUNNING_MODAL'}

class GLAImport(bpy.types.Operator):
        '''Import GLA Operator.'''
        bl_idname = "import_scene.gla"
        bl_label = "Import Ghoul 2 Skeleton (.gla)"
        bl_description = "Imports a Ghoul 2 skeleton (.gla) and optionally the animation."
        bl_options = {'REGISTER', 'UNDO'}

        filepath = bpy.props.StringProperty(name="File Path", description="The .gla file to import", maxlen=1024, default="")

        def execute(self, context):
            #todo
            #    self.report({'ERROR'}, message)
            return {'FINISHED'}

        def invoke(self, context, event):
            wm= context.window_manager
            wm.fileselect_add(self)
            return {'RUNNING_MODAL'}

class GLMExport(bpy.types.Operator):
        '''Export GLM Operator.'''
        bl_idname = "export_scene.glm"
        bl_label = "Export Ghoul 2 Model (.glm)"
        bl_description = "Exports a Ghoul 2 model (.glm)"
        bl_options = {'REGISTER', 'UNDO'}

        filepath = bpy.props.StringProperty(name="File Path", description="The filename to export to", maxlen=1024, default="")

        def execute(self, context):
            #todo
            #    self.report({'ERROR'}, message)
            return {'FINISHED'}

        def invoke(self, context, event):
            wm= context.window_manager
            wm.fileselect_add(self)
            return {'RUNNING_MODAL'}

class GLAExport(bpy.types.Operator):
        '''Export GLA Operator.'''
        bl_idname = "export_scene.gla"
        bl_label = "Export Ghoul 2 Skeleton & Animation (.gla)"
        bl_description = "Exports a Ghoul 2 Skeleton and its animations (.gla)"
        bl_options = {'REGISTER', 'UNDO'}

        filepath = bpy.props.StringProperty(name="File Path", description="The filename to export to", maxlen=1024, default="")

        def execute(self, context):
            #todo
            #    self.report({'ERROR'}, message)
            return {'FINISHED'}

        def invoke(self, context, event):
            wm= context.window_manager
            wm.fileselect_add(self)
            return {'RUNNING_MODAL'}

class ObjectAddG2Properties(bpy.types.Operator):
    bl_idname = "object.add_g2_properties"
    bl_label = "Add G2 properties"
    bl_description = "Adds Ghoul 2 properties"

    def execute(self, context):
        obj = context.object
        # don't overwrite those that already exist
        if not "g2_prop_off" in obj:
            obj.g2_prop_off = False
        if not "g2_prop_tag" in obj:
            obj.g2_prop_tag = False
        if not "g2_prop_name" in obj:
            obj.g2_prop_name = ""
        return{'FINISHED'}

class ObjectRemoveG2Properties(bpy.types.Operator):
    bl_idname = "object.remove_g2_properties"
    bl_label = "Remove G2 properties"
    bl_description = "Removes Ghoul 2 properties"

    def execute(self, context):
        obj = context.object
        bpy.types.Object.__delitem__(obj, "g2_prop_off")
        bpy.types.Object.__delitem__(obj, "g2_prop_tag")
        bpy.types.Object.__delitem__(obj, "g2_prop_name")
        return{'FINISHED'}

# menu button callback functions
def menu_func_export_glm(self, context):
    self.layout.operator(mrw_g2_operators.GLMExport.bl_idname, text="Ghoul 2 model (.glm)")

def menu_func_export_gla(self, context):
    self.layout.operator(mrw_g2_operators.GLAExport.bl_idname, text="Ghoul 2 skeleton/animation (.gla)")
    
def menu_func_import_glm(self, context):
    self.layout.operator(mrw_g2_operators.GLMImport.bl_idname, text="Ghoul 2 model (.glm)")

def menu_func_import_gla(self, context):
    self.layout.operator(mrw_g2_operators.GLAImport.bl_idname, text="Ghoul 2 skeleton/animation (.gla)")

# menu button init/destroy
def register():
    bpy.types.INFO_MT_file_export.append(menu_func_export_glm)
    bpy.types.INFO_MT_file_export.append(menu_func_export_gla)
    bpy.types.INFO_MT_file_import.append(menu_func_import_glm)
    bpy.types.INFO_MT_file_import.append(menu_func_import_gla)

def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_func_export_glm)
    bpy.types.INFO_MT_file_export.remove(menu_func_export_gla)
    bpy.types.INFO_MT_file_import.remove(menu_func_import_glm)
    bpy.types.INFO_MT_file_import.remove(menu_func_import_gla)