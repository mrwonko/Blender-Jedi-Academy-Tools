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

# reads a string stored as 64 bit NULL-terminated, returns as normal string
def toQ3String(binaryData):
    bs, = struct.unpack("64s", binaryData)
    # \0 prefix is probably to force usage of .skin files
    # but ModView can deal with it so I do so, too.
    #TODO: add proper support for skin files instead.
    if bs[:7] == b"\0odels/":
        bs = b"m" + bs[1:]
    if bs[:12] == b"\0omaterial]":
        bs = b"[" + bs[1:]
    end = bs.find(b"\0") # removing \0's from the right doesn't cut it - sometimes there's something after the first NULL.
    if end == -1:
        return bs.decode()
    return bs[:end].decode()
