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
