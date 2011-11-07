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

from . import mrw_g2_filesystem
import bpy

class MaterialManager():
    def __init__(self, basepath):
        self.basepath = basepath
        self.materials = {}
    
    def getMaterial(self, name):
        assert(name != "[nomaterial]")
        if name.lower() in self.materials:
            return self.materials[name.lower()]
        # create material, it doesn't exist yet
        mat = bpy.data.materials.new(name)
        self.materials[name.lower()] = mat
        # try to find the image
        success, path = mrw_g2_filesystem.FindFile(name, self.basepath, ["jpg", "png", "tga"])
        # if it doesn't exist, we're done.
        if not success:
            print("Texture not found: \"", name, "\"", sep="")
            # make it pink though
            mat.diffuse_color = (1, 0, 1)
            return mat
        
        #load image
        img = bpy.data.images.load(path)
        #create a texture with it
        tex = bpy.data.textures.new(name, type='IMAGE')
        tex.image = img
        # create texture slot
        tex_slot = mat.texture_slots.add()
        tex_slot.texture_coords = 'UV'
        tex_slot.texture = tex
        
        return mat
