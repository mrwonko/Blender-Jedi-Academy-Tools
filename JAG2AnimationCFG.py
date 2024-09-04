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

from .mod_reload import reload_modules
reload_modules(locals(), __package__, ["JAFilesystem"], [".casts", ".error_types"])  # nopep8

import bpy
from . import JAFilesystem
from .error_types import ErrorMessage
from typing import List, Tuple


class AnimationSequence():
    def __init__(self):
        self.name = ""
        self.start_frame = -1
        self.num_frames = -1
        self.loop = False
        self.fps = -1

    def __str__(self):
        return "{name}\t\t{start}\t{frames}\t{loop}\t{fps}".format(
            name = self.name,
            start = self.start_frame,
            frames = self.num_frames,
            loop = 0 if self.loop else -1,
            fps = self.fps
        )

    @classmethod
    def from_cfg_line(cls, txt_line):
        try:
            # remove comments inline first, someone might have annotated these
            line = txt_line.split("//")[0]
            name, sf, nf, l, fps = line.split()
            new_frame = cls()
            new_frame.name = name
            new_frame.start_frame = int(sf)
            new_frame.num_frames = int(nf)
            new_frame.loop = int(l) != -1
            new_frame.fps = int(fps)
            return new_frame
        except Exception:
            return None
        
    @classmethod
    def from_blender_markers(cls, marker1, marker2, fps, offset = 0):
        new_frame = cls()
        new_frame.name = marker1.name
        new_frame.start_frame = int(marker1.frame + offset)
        new_frame.num_frames = int(marker2.frame - marker1.frame)
        new_frame.loop = False
        new_frame.fps = int(fps)
        return new_frame
    
    @classmethod
    def from_blender_strip(cls, nla_strip, length_difference, fps, offset = 0):
        new_frame = cls()
        new_frame.name = nla_strip.action.name
        new_frame.start_frame = int(nla_strip.frame_start + offset)
        new_frame.num_frames = int(nla_strip.frame_end - nla_strip.frame_start + length_difference)
        new_frame.loop = False
        new_frame.fps = int(fps)
        return new_frame


class AnimationCGF():

    def __init__(self):
        self.sequences : List[AnimationSequence] = []

    def __str__(self):
        lines = [str(seq) for seq in self.sequences]
        return "\n".join(lines)

    def load_from_cfg(self, cfg_file_path) -> Tuple[bool, ErrorMessage]:
        success, cfg_abs = JAFilesystem.FindFile(cfg_file_path + "/animation", "", ["cfg"])
        if not success:
            print("Could not find file: ", cfg_abs, sep="")
            return False, ErrorMessage("Could not find the animation.cfg next to the .gla file")
        
        try:
            file = open(cfg_abs, mode="r")
        except IOError:
            print("Could not open file: ", cfg_abs, sep="")
            return False, ErrorMessage("Could not open skin!")
        for line in file:
            if line.startswith("//") or line.strip() == "":
                continue
            seqence = AnimationSequence().from_cfg_line(line)
            if seqence:
                self.sequences.append(seqence)
            else:
                print("Could not parse following line in animations.cfg", line)
        self.sequences.sort(key=lambda sequence: sequence.start_frame)
        return True, ErrorMessage("Nothing")
    
    def from_blender_markers(self, context, offset):
        start_frame = context.scene.frame_start
        offset -= start_frame
        end_frame = context.scene.frame_end
        base_fps = context.scene.render.fps

        blender_markers = [
            marker for marker in context.scene.timeline_markers if (
                marker.frame >= start_frame and marker.frame <= end_frame+1)
            ]
        blender_markers.sort(key=lambda marker: marker.frame)

        if (len(blender_markers) == 0 or 
            (len(blender_markers) == 1 and blender_markers[0].frame == end_frame+1)):
            return False, ErrorMessage("No timeline markers found! Add Markers to label animations.")

        if blender_markers[len(blender_markers)-1].frame != end_frame+1:
            blender_markers.append(
                context.scene.timeline_markers.new("LAST_EXPORT_FRAME", frame = end_frame+1))

        for marker1, marker2 in zip(blender_markers[:-1], blender_markers[1:]):
            self.sequences.append(AnimationSequence().from_blender_markers(
                marker1,
                marker2,
                base_fps,
                offset
            ))

        last_frame = context.scene.timeline_markers.get("LAST_EXPORT_FRAME")
        if last_frame:
            context.scene.timeline_markers.remove(last_frame)

        return True, ErrorMessage("Nothing")
    
    def from_blender_nla_tracks(self, context, offset):
        start_frame = context.scene.frame_start
        offset -= start_frame
        end_frame = context.scene.frame_end
        base_fps = context.scene.render.fps

        skeleton_object = bpy.data.objects.get("skeleton_root")
        if skeleton_object is None:
            return False, ErrorMessage("Could not find skeleton object: skeleton_root")
        if skeleton_object.animation_data is None:
            return False, ErrorMessage('Skeleton object (skeleton_root) does not have animation data')
        if len(skeleton_object.animation_data.nla_tracks) == 0:
            return False, ErrorMessage("Couldn't find NLA tracks for the Skeleton object: skeleton_root")

        blender_strips = []
        for nla_track in [track for track in skeleton_object.animation_data.nla_tracks]:
            length_differnce = 0 if nla_track.name.startswith("Stills Layer") else 1
            for nla_strip in [strip for strip in nla_track.strips if strip.frame_start >= start_frame and strip.frame_start <= end_frame]:
                blender_strips.append((nla_strip, length_differnce))
        blender_strips.sort(key=lambda strip: strip[0].frame_start)

        if len(blender_strips) == 0:
            return False, ErrorMessage("No NLA strips found! Add animation strips to label animations.")

        for strip, length_differnce in blender_strips:
            self.sequences.append(AnimationSequence().from_blender_strip(
                strip,
                length_differnce,
                base_fps,
                offset
            ))

        return True, ErrorMessage("Nothing")
        