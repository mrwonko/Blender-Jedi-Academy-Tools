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

class GLA:
    #whether this is the automatic default skeleton
    isDefault = False
    
    def __init__(self):
        pass
    
    def loadFromFile(self, filepath_abs):
        #todo
        return True, ""
    
    def loadFromBlender(self, gla_filepath_rel, scene_root):
        #todo
        return True, ""
    
    def saveToFile(self, filepath_abs):
        #todo
        return True, ""
    
    def saveToBlender(self, scene_root):
        #todo
        return True, ""
