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

# length of file path strings
from enum import Enum
from typing import Dict, List


MAX_QPATH = 64  # cannot be changed without adjusting file format & engine

# gla format
GLA_IDENT = b"2LGA"
GLA_VERSION = 6

# glm format
GLM_IDENT = b'2LGM'
GLM_VERSION = 6

SURFACEFLAG_TAG = 0b1
SURFACEFLAG_OFF = 0b10

BONELENGTH = 4

# 0.999 = cos 2.5, 0.996 = cos 5, 0.990 = cos 8
# 0.999 is okay for the player model (_humanoid), but the atst is somewhat less exact
# cosine of allowed angle between bone directions for them to be considered equal
BONE_ANGLE_ERROR_MARGIN = 0.996

# CompBone's compressed frame translation is quantized to this many steps per unit (see
# JAG2Math.CompBone.loadFromFile/compress) - the smallest movement a compressed frame can
# represent along a single axis.
COMPBONE_LOCATION_STEPS_PER_UNIT = 64
COMPBONE_LOCATION_QUANTUM = 1 / COMPBONE_LOCATION_STEPS_PER_UNIT

# max distance (game units) a bone's actual per-frame head position may drift from where a
# rigidly-connected bone's head would be (the parent's tail, following the parent's rotation)
# before we consider it to need independent translation - use_connect can't represent that.
# _boneCanConnect compares positions reconstructed from compressed (quantized) frame data through
# a chain of ancestor transforms, so quantization/floating-point noise can compound across the
# hierarchy - a few quantization steps of wiggle room comfortably covers that without masking a
# real, consistently-drifting translation.
BONE_TRANSLATION_ERROR_MARGIN = 3 * COMPBONE_LOCATION_QUANTUM


class SkeletonFixes(Enum):
    NONE = 'NONE'
    JKA_HUMANOID = 'JKA_HUMANOID'


# bones to which the parent (with multiple children) should preferably connect
PRIORITY_BONES: Dict[SkeletonFixes, List[str]] = {
    SkeletonFixes.NONE: [],
    SkeletonFixes.JKA_HUMANOID: [
        # legs - ignore [lr]femurX
        "rtibia",
        "ltibia",
        # arms
        # ignore [lr]humerusX
        "rradius",
        "lradius",
        # ignore [lr]radiusX (and all the hand stuff)
        "rhand",
        "lhand",
        # spine - ignore shoulders and legs
        "cervical",
        "lower_lumbar"
    ]
}

# bones that get different parents
# bone index -> new parent index
PARENT_CHANGES: Dict[SkeletonFixes, Dict[int, int]] = {
    SkeletonFixes.NONE: {},
    SkeletonFixes.JKA_HUMANOID: {
        #  shoulder fixes
        25: 24,  # rhumerus gets parent rclavical
        38: 37,  # lhumerus gets parent lclavical

        #  hand fixes
        # r_d[124]_j1 to rhand
        30: 29,
        32: 29,
        34: 29,
        36: 29,  # rhang_tag_bone to rhand
        # r_d[124]_j2 to r_d[124]_j2
        31: 30,
        33: 32,
        35: 34,
        # l_d[124]_j1 to lhand
        43: 42,
        45: 42,
        47: 42,
        51: 42,  # lhang_tag_bone to lhand
        # l_d[124]_j2 to l_d[124]_j2
        44: 43,
        46: 45,
        48: 47
    }
}
