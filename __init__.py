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

#  Imports

from .mod_reload import reload_modules
reload_modules(locals(), __package__, ["JAAseExport", "JAAseImport", "JAPatchExport", "JARoffImport", "JARoffExport", "JAG2Panels", "JAG2Operators"], [])  # nopep8

#  Blender
import bpy

#  Local
# ASE
from . import JAAseExport
from . import JAAseImport
# Patch
from . import JAPatchExport
# ROFF
from . import JARoffImport
from . import JARoffExport
# Ghoul 2
from . import JAG2Panels
from . import JAG2Operators

bl_info = {
    "name": "Jedi Academy Import/Export Tools",
    "author": "mrwonko, Cagelight et al",
    "description": "Various Jedi Knight: Jedi Academy related tools: Importers for ASE, GLA, GLM, ROFF and Exporters for ASE, GLA, GLM, animation.cfg, ROFF",
    "blender": (4, 1, 0),
    "location": "File > Import-Export",
    "category": "Import-Export"
}

# there must be at least one operator in the locals for Blender to reload correctly.
JAAseExportOp = JAAseExport.Operator


def register():
    bpy.utils.register_class(JAAseExport.Operator)
    bpy.utils.register_class(JAPatchExport.Operator)
    bpy.utils.register_class(JARoffExport.Operator)
    bpy.utils.register_class(JAAseImport.Operator)
    bpy.utils.register_class(JARoffImport.Operator)
    bpy.utils.register_class(JAG2Panels.G2PropertiesPanel)

    JAG2Panels.initG2Properties()
    JAG2Operators.register()

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
    bpy.utils.unregister_class(JAG2Panels.G2PropertiesPanel)

    JAG2Operators.unregister()

    bpy.types.TOPBAR_MT_file_export.remove(JAAseExport.menu_func)
    bpy.types.TOPBAR_MT_file_export.remove(JAPatchExport.menu_func)
    bpy.types.TOPBAR_MT_file_export.remove(JARoffExport.menu_func)

    bpy.types.TOPBAR_MT_file_import.remove(JAAseImport.menu_func)
    bpy.types.TOPBAR_MT_file_import.remove(JARoffImport.menu_func)


if __name__ == "__main__":
    register()
