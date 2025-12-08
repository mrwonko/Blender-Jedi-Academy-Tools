# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software...
#
# ##### END GPL LICENSE BLOCK #####

from .mod_reload import reload_modules
reload_modules(locals(), __package__, [
    "JAAseExport",
    "JAAseImport",
    "JAPatchExport",
    "JARoffImport",
    "JARoffExport",
    "JAG2Panels",
    "JAG2Operators"
], [])

import bpy

from . import JAAseExport
from . import JAAseImport
from . import JAPatchExport
from . import JARoffImport
from . import JARoffExport
from . import JAG2Panels
from . import JAG2Operators

bl_info = {
    "name": "Jedi Academy Import/Export Tools",
    "author": "mrwonko, Cagelight et al",
    "description": "Tools for importing/exporting JKJA formats",
    "blender": (4, 1, 0),
    "location": "File > Import-Export",
    "category": "Import-Export"
}

# Required placeholder for reload
JAAseExportOp = JAAseExport.Operator


def register():

    # Register import/export operators
    bpy.utils.register_class(JAAseExport.Operator)
    bpy.utils.register_class(JAPatchExport.Operator)
    bpy.utils.register_class(JARoffExport.Operator)
    bpy.utils.register_class(JAAseImport.Operator)
    bpy.utils.register_class(JARoffImport.Operator)

    # Register Ghoul2 system (PropertyGroup + panel + operators)
    JAG2Panels.register()
    JAG2Operators.register()

    # Menu entries
    bpy.types.TOPBAR_MT_file_export.append(JAAseExport.menu_func)
    bpy.types.TOPBAR_MT_file_export.append(JAPatchExport.menu_func)
    bpy.types.TOPBAR_MT_file_export.append(JARoffExport.menu_func)

    bpy.types.TOPBAR_MT_file_import.append(JAAseImport.menu_func)
    bpy.types.TOPBAR_MT_file_import.append(JARoffImport.menu_func)


def unregister():

    bpy.utils.unregister_class(JAAseExport.Operator)
    bpy.utils.unregister_class(JAPatchExport.Operator)
    bpy.utils.unregister_class(JARoffExport.Operator)
    bpy.utils.unregister_class(JAAseImport.Operator)
    bpy.utils.unregister_class(JARoffImport.Operator)

    JAG2Panels.unregister()
    JAG2Operators.unregister()

    bpy.types.TOPBAR_MT_file_export.remove(JAAseExport.menu_func)
    bpy.types.TOPBAR_MT_file_export.remove(JAPatchExport.menu_func)
    bpy.types.TOPBAR_MT_file_export.remove(JARoffExport.menu_func)

    bpy.types.TOPBAR_MT_file_import.remove(JAAseImport.menu_func)
    bpy.types.TOPBAR_MT_file_import.remove(JARoffImport.menu_func)


if __name__ == "__main__":
    register()
