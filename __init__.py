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

bl_info = {
    "name": "Ghoul 2 format (.glm/.gla)",
    "author": "Willi Schinmeyer",
    "blender": (2, 6, 0),
    "api": 41226,
    "location": "File > Export",
    "description": "Imports and exports Ghoul 2 models and animations.",
    "warning": "",
    #"wiki_url": "",
    "tracker_url": "https://github.com/mrwonko/Blender-2.6-Ghoul-2-addon/issues",
    #"support": 'OFFICIAL',
    "category": "Import-Export"
}

# To support reload properly, try to access a package var, if it's there, reload everything
# i.e. reload stuff loaded via import
if "bpy" in locals():
    import imp
    #if "export_map" in locals(): #todo: replace with names of my module(s)
    #    imp.reload(export_map)

import bpy
from bpy.props import StringProperty #, FloatProperty, BoolProperty, EnumProperty

class OperatorGLMImport(bpy.types.Operator):
		'''Import GLM Operator.'''
		bl_idname = "import_scene.glm"
		bl_label = "Import Ghoul 2 Model (.glm)"
		bl_description = "Imports a Ghoul 2 model (.glm), looking up the skeleton (and optionally the animation) from the referenced (or optionally a different) .gla file."
		bl_options = {'REGISTER', 'UNDO'}

		filepath = StringProperty(name="File Path", description="The .glm file to import", maxlen=1024, default="")

		def execute(self, context):
			print("Import:", self.filepath)
			#todo
			#	self.report({'ERROR'}, message)
			return {'FINISHED'}

		def invoke(self, context, event):
			wm= context.window_manager
			wm.fileselect_add(self)
			return {'RUNNING_MODAL'}

class OperatorGLAImport(bpy.types.Operator):
		'''Import GLA Operator.'''
		bl_idname = "import_scene.gla"
		bl_label = "Import Ghoul 2 Skeleton (.gla)"
		bl_description = "Imports a Ghoul 2 skeleton (.gla) and optionally the animation."
		bl_options = {'REGISTER', 'UNDO'}

		filepath = StringProperty(name="File Path", description="The .gla file to import", maxlen=1024, default="")

		def execute(self, context):
			#todo
			#	self.report({'ERROR'}, message)
			return {'FINISHED'}

		def invoke(self, context, event):
			wm= context.window_manager
			wm.fileselect_add(self)
			return {'RUNNING_MODAL'}

class OperatorGLMExport(bpy.types.Operator):
		'''Export GLM Operator.'''
		bl_idname = "export_scene.glm"
		bl_label = "Export Ghoul 2 Model (.glm)"
		bl_description = "Exports a Ghoul 2 model (.glm)"
		bl_options = {'REGISTER', 'UNDO'}

		filepath = StringProperty(name="File Path", description="The filename to export to", maxlen=1024, default="")

		def execute(self, context):
			#todo
			#	self.report({'ERROR'}, message)
			return {'FINISHED'}

		def invoke(self, context, event):
			wm= context.window_manager
			wm.fileselect_add(self)
			return {'RUNNING_MODAL'}

class OperatorGLAExport(bpy.types.Operator):
		'''Export GLA Operator.'''
		bl_idname = "export_scene.gla"
		bl_label = "Export Ghoul 2 Skeleton & Animation (.gla)"
		bl_description = "Exports a Ghoul 2 Skeleton and its animations (.gla)"
		bl_options = {'REGISTER', 'UNDO'}

		filepath = StringProperty(name="File Path", description="The filename to export to", maxlen=1024, default="")

		def execute(self, context):
			#todo
			#	self.report({'ERROR'}, message)
			return {'FINISHED'}

		def invoke(self, context, event):
			wm= context.window_manager
			wm.fileselect_add(self)
			return {'RUNNING_MODAL'}

def menu_func_export_glm(self, context):
    self.layout.operator(OperatorGLMExport.bl_idname, text="Ghoul 2 model (.glm)")

def menu_func_export_gla(self, context):
    self.layout.operator(OperatorGLAExport.bl_idname, text="Ghoul 2 skeleton/animation (.gla)")
	
def menu_func_import_glm(self, context):
    self.layout.operator(OperatorGLMImport.bl_idname, text="Ghoul 2 model (.glm)")

def menu_func_import_gla(self, context):
    self.layout.operator(OperatorGLAImport.bl_idname, text="Ghoul 2 skeleton/animation (.gla)")


def register():
    bpy.utils.register_module(__name__)


#called when the plugin is activated
def register():
    bpy.utils.register_module(__name__)
	#add menu buttons
    bpy.types.INFO_MT_file_export.append(menu_func_export_glm)
    bpy.types.INFO_MT_file_export.append(menu_func_export_gla)
    bpy.types.INFO_MT_file_import.append(menu_func_import_glm)
    bpy.types.INFO_MT_file_import.append(menu_func_import_gla)

#called when the plugin is deactivated
def unregister():
    bpy.utils.unregister_module(__name__)
	#remove menu buttons
    bpy.types.INFO_MT_file_export.remove(menu_func_export_glm)
    bpy.types.INFO_MT_file_export.remove(menu_func_export_gla)
    bpy.types.INFO_MT_file_import.remove(menu_func_import_glm)
    bpy.types.INFO_MT_file_import.remove(menu_func_import_gla)

# register it if script is called directly	
if __name__ == "__main__":
    register()