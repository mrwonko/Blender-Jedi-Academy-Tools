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

#Blender Python
import bpy

# To support reload properly, try to access a package var, if it's there, reload everything
if "bpy" in locals():
    import imp

    # Reload Operators
    if "mrw_g2_operators" in locals(): #already loaded?
        imp.reload(mrw_g2_operators) #then: reload
    else:
        from . import mrw_g2_operators

    # Reload Menu Panel
    if "mrw_g2_panels" in locals(): #already loaded?
        imp.reload(mrw_g2_panels) #then: reload
    else:
        from . import mrw_g2_panels
else:
    from . import mrw_g2_operators
    from . import mrw_g2_panels




def menu_func_export_glm(self, context):
    self.layout.operator(mrw_g2_operators.GLMExport.bl_idname, text="Ghoul 2 model (.glm)")

def menu_func_export_gla(self, context):
    self.layout.operator(mrw_g2_operators.GLAExport.bl_idname, text="Ghoul 2 skeleton/animation (.gla)")
    
def menu_func_import_glm(self, context):
    self.layout.operator(mrw_g2_operators.GLMImport.bl_idname, text="Ghoul 2 model (.glm)")

def menu_func_import_gla(self, context):
    self.layout.operator(mrw_g2_operators.GLAImport.bl_idname, text="Ghoul 2 skeleton/animation (.gla)")


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
    #add panels
    #apparently happens automatically, I get an error if I try to do it myself.
    #bpy.utils.register_class(mrw_g2_panels.G2PropertiesPanel)

#called when the plugin is deactivated
def unregister():
    bpy.utils.unregister_module(__name__)
    #remove menu buttons
    bpy.types.INFO_MT_file_export.remove(menu_func_export_glm)
    bpy.types.INFO_MT_file_export.remove(menu_func_export_gla)
    bpy.types.INFO_MT_file_import.remove(menu_func_import_glm)
    bpy.types.INFO_MT_file_import.remove(menu_func_import_gla)
    #remove panels
    #bpy.utils.unregister_class(mrw_g2_panels.G2PropertiesPanel)

# register it if script is called directly    
if __name__ == "__main__":
    register()