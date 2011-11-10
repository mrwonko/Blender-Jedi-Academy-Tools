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

import struct
import mathutils

# 3 * 4 : shear not used.
class Matrix:
    def __init__(self):
        self.rows = []
        for i in range(3):
            self.rows.append([0, 0, 0, 0])
        self.rows[0][0] = 1
        self.rows[1][1] = 1
        self.rows[2][2] = 1
    
    def loadFromFile(self, file):
        for y in range(3):
            for x in range(4):
                self.rows[y][x], = struct.unpack("f", file.read(4))
    
    def saveToFile(self, file):
        for y in range(3):
            for x in range(4):
                file.write(struct.pack("f", self.rows[y][x]))
    
    #todo: toBlender()/fromBlender(blenderMat)
    def toBlender(self):
        mat = mathutils.Matrix([self.rows[0], self.rows[1], self.rows[2], [0, 0, 0, 1]])
        mat.transpose() # row major <-> col major
        return mat
    
    def fromBlender(self, mat):
        mat = mathutils.Matrix(mat)
        mat.transpose() # row major <-> col major
        if mat.row_size != 4 or mat.col_size != 4:
            mat.to_4x4()
        self.rows = []
        for row in mat:
            l = []
            l.extend(row)
            self.rows.append(l)
        del self.rows[3]

# compressed bones as used in GLA files
#todo
class CompBone:
    def __init__(self):
        self.quat = mathutils.Quaternion()
        self.loc = mathutils.Vector()
    
    def loadFromFile(self, file):
        # 14 bytes: 4 shorts for quat = 8 bytes, 3 shorts for position = 6 bytes
        q_w, q_x, q_y, q_z, l_x, l_y, l_z = struct.unpack("7H", file.read(14))
        # map quaternion values from 0..65535 to -2..2
        self.quat.w = (q_w / 16383) - 2
        self.quat.x = (q_x / 16383) - 2
        self.quat.y = (q_y / 16383) - 2
        self.quat.z = (q_z / 16383) - 2
        # map location from 0..65535 to -512..512 (511.984375)
        self.loc.x = (l_x / 64) - 512
        self.loc.y = (l_y / 64) - 512
        self.loc.z = (l_z / 64) - 512
    
    def saveToFile(self, file):
        file.write(struct.pack("7H",
            round((self.quat.w+2)*16383),
            round((self.quat.x+2)*16383),
            round((self.quat.y+2)*16383),
            round((self.quat.z+2)*16383),
            round((self.loc.x+512)*64),
            round((self.loc.y+512)*64),
            round((self.loc.z+512)*64)))
