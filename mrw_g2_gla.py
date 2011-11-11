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

from . import mrw_g2_stringhelpers, mrw_g2_constants, mrw_g2_math
import struct, bpy, mathutils

def readString(file):
    return mrw_g2_stringhelpers.decode(struct.unpack("64s", file.read(mrw_g2_constants.MAX_QPATH))[0])

class MdxaHeader:
    
    def __init__(self):
        self.name = ""
        self.scale = 0
        self.numFrames = -1
        self.ofsFrames = -1
        self.numBones = -1
        self.ofsCompBonePool = -1
        self.ofsSkel = -1 # this is also MdxaSkelOffsets.baseOffset + MdxaSkelOffsets.boneOffsets[0] - probably a historic leftover
        self.ofsEnd = -1
    
    def loadFromFile(self, file):
        # check ident
        ident, = struct.unpack("4s", file.read(4))
        if ident != mrw_g2_constants.GLA_IDENT:
            print("File does not start with ", mrw_g2_constants.GLA_IDENT, " but ", ident, " - no GLA!")
            return False, "Is no GLA file!"
        version, = struct.unpack("i", file.read(4))
        if version != mrw_g2_constants.GLA_VERSION:
            return False, "Wrong gla file version! ("+str(version)+" should be "+str(mrw_g2_constants.GLA_VERSION)+")"
        name = readString(file)
        self.scale, self.numFrames, self.ofsFrames, self.numBones, self.ofsCompBonePool, self.ofsSkel, self.ofsEnd = struct.unpack("f6i", file.read(7*4))
        return True, ""

class MdxaBoneOffsets:
    
    def __init__(self):
        self.baseOffset = 2*4 + 64 + 4*7 #sizeof header
        self.boneOffsets = []
    
    # fail-safe (except exceptions)
    def loadFromFile(self, file, numBones):
        assert(self.baseOffset == file.tell())
        for i in range(numBones):
            self.boneOffsets.append(struct.unpack("i", file.read(4))[0])

# originally called MdxaSkel_t, but I find that name misleading
class MdxaBone:
    def __init__(self):
        self.name = ""
        self.flags = -1
        self.parent = -1
        self.basePoseMat = mrw_g2_math.Matrix()
        self.basePoseMatInv = mrw_g2_math.Matrix()
        self.numChildren = -1
        self.children = []
        self.index = -1 # not saved, filled by loadBonesFromFile()
    
    def loadFromFile(self, file):
        self.name = readString(file)
        self.flags, self.parent = struct.unpack("Ii", file.read(2*4))
        self.basePoseMat.loadFromFile(file)
        self.basePoseMatInv.loadFromFile(file)
        self.numChildren, = struct.unpack("i", file.read(4))
        for i in range(self.numChildren):
            self.children.append(struct.unpack("i", file.read(4))[0])
    
    #blenderBonesSoFar is a dictionary of boneIndex -> BlenderBone
    #allBones is the list of all MdxaBones
    #use it to set up hierarchy and add yourself once done.
    def saveToBlender(self, armature, blenderBonesSoFar, allBones, skeletonFixes):
        # create bone 
        bone = armature.edit_bones.new(self.name)
        
        # set position
        mat = self.basePoseMat.toBlender()
        pos = mathutils.Vector(mat[3][:3])
        bone.head = pos
        # head is offset a bit.
        x_axis = mathutils.Vector(mat[0][0:3]) # X points towards next bone.
        bone.tail = pos + x_axis*mrw_g2_constants.BONELENGTH
        # set roll
        z_axis = mathutils.Vector(mat[2][0:3])
        bone.align_roll(z_axis)
        
        # set parent, if any, keeping in mind it might be overwritten
        parentIndex = self.parent
        parentChanges = mrw_g2_constants.PARENT_CHANGES[skeletonFixes]
        if self.index in parentChanges:
            parentIndex = parentChanges[self.index]
        if parentIndex != -1:
            blenderParent = blenderBonesSoFar[parentIndex]
            bone.parent = blenderParent
            
            #how many children does the parent have?
            numParentChildren = allBones[parentIndex].numChildren
            # we actually need to take into account the hierarchy changes.
            # so for any bone that used to have this parent but does not anymore, remove one
            for mdxaBone in allBones:
                # if a bone gets its parent changed, and it used to be "my" parent, my parent has one child less.
                if mdxaBone.parent == parentIndex and mdxaBone.index in parentChanges:
                    numParentChildren -= 1
            assert(numParentChildren >= 0)
            # and for any bone that got this as the parent, add one child.
            for _, newParentIndex in parentChanges.items():
                if newParentIndex == parentIndex:
                    numParentChildren += 1
            assert(numParentChildren > 0) #at least this bone is child.
            
            # if this is the only child of its parent or has priority: Connect the parent to this.
            if numParentChildren == 1 or self.name in mrw_g2_constants.PRIORITY_BONES[skeletonFixes]:
                # but only if that doesn't rotate the bone (much)
                # so calculate the directions...
                oldDir = blenderParent.tail - blenderParent.head
                newDir = pos - blenderParent.head
                oldDir.normalize()
                newDir.normalize()
                dotProduct = oldDir.dot(newDir)
                # ... and compare them using the dot product, which is the cosine of the angle between two unit vectors
                if dotProduct > mrw_g2_constants.BONE_ANGLE_ERROR_MARGIN:
                    blenderParent.tail = pos
                    bone.use_connect = True
        
        # save to created bones
        blenderBonesSoFar[self.index] = bone

class MdxaSkel:
    def __init__(self):
        self.bones = []
        self.armature = None
        self.armatureObject = None
        # Blender Bones by index - used by Animation
        self.blenderBones = {}
    
    def loadFromFile(self, file, offsets):
        for i, offset in enumerate(offsets.boneOffsets):
            file.seek(offsets.baseOffset + offset)
            bone = MdxaBone()
            bone.loadFromFile(file)
            bone.index = i
            self.bones.append(bone)
    
    def saveToFile(self, file):
        pass
    
    def fitsArmature(self, armature):
        for bone in self.bones:
            if not bone.name in armature.bones:
                return False, "Bone "+bone.name+" not found in existing skeleton_root armature!"
            return True, ""
    
    def saveToBlender(self, scene_root, skeletonFixes):
        #  Creation
        #create armature
        self.armature = bpy.data.armatures.new("skeleton_root")
        #create object
        self.armature_object = bpy.data.objects.new("skeleton_root", self.armature)
        #set parent
        self.armature_object.parent = scene_root
        #link object to scene
        bpy.context.scene.objects.link(self.armature_object)
        
        #  Set the armature as active and go to edit mode to add bones
        bpy.context.scene.objects.active = self.armature_object
        bpy.ops.object.mode_set(mode='EDIT')
        # list of indices of already created bones - only those bones with this as parent will be added
        createdBonesIndices = [-1]
        # bones yet to be created
        uncreatedBones = []
        uncreatedBones.extend(self.bones)
        parentChanges = mrw_g2_constants.PARENT_CHANGES[skeletonFixes]
        while len(uncreatedBones) > 0:
            # whether a new bone was created this time - if not, there's a hierarchy problem
            createdBone = False
            newUncreatedBones = []
            for bone in uncreatedBones:
                # only create those bones whose parent has already been created.
                if bone.index in parentChanges:
                    parent = parentChanges[bone.index]
                else:
                    parent = bone.parent
                if parent in createdBonesIndices:
                    bone.saveToBlender(self.armature, self.blenderBones, self.bones, skeletonFixes)
                    createdBonesIndices.append(bone.index)
                    createdBone = True
                else:
                    newUncreatedBones.append(bone)
            uncreatedBones = newUncreatedBones
            if not createdBone:
                bpy.ops.object.mode_set(mode='OBJECT')
                return False, "gla has hierarchy problems!"
        # leave armature edit mode
        bpy.ops.object.mode_set(mode='OBJECT')
        return True, ""

class MdxaFrame:
    def __init__(self):
        self.boneIndices = []
    
    # returns the highest referenced index - not nice from a design standpoint but saves space, which is probably good.
    def loadFromFile(self, file, numBones):
        maxIndex = 0
        for i in range(numBones):
            # bone indices are only 3 bytes long - with 30k+ frames 25% less is quite a bit, reportedly.
            index, = struct.unpack("i", file.read(3)+b"\0")
            maxIndex = max(maxIndex, index)
            self.boneIndices.append(index)
        return maxIndex
    
    def saveToFile(self, file):
        for index in self.boneIndices:
            # only write the first 3 bytes of the packed number
            file.write(struct.pack("i", index)[:3])

class MdxaBonePool:
    def __init__(self):
        # during import, this is a list of CompBone objects
        # during exports, it's a list of 14-byte-objects (compressed bones)
        self.bones = []
    
    def loadFromFile(self, file, numCompBones):
        self.bones = [mrw_g2_math.CompBone().loadFromFile(file) for i in range(numCompBones)]
        """
        for i in range(numCompBones):
            compBone = mrw_g2_math.CompBone()
            compBone.loadFromFile(file)
            self.bones.append(compBone)
        """
    
    def saveToFile(self, file):
        for bone in self.bones:
            bone.saveToFile(file)

# Frames & Compressed Bone Pool
class MdxaAnimation:
    def __init__(self):
        self.frames = []
        self.bonePool = MdxaBonePool()
    
    def loadFromFile(self, file, header, skeleton):
        # read frames
        if file.tell() != header.ofsFrames:
            print("Info: Frames in .gla not encountered when expected (at ", file.tell(), " instead of ", header.ofsFrames, "), seeking correct position. There could be a bug in the importer (bad) or the file could be unusual - but not necessarily wrong (no problem).", sep="")
            file.seek(header.ofsFrames)
        maxIndex = -1
        for i in range(header.numFrames):
            frame = MdxaFrame()
            # loadFromFile returns highest read index
            maxIndex = max(maxIndex, frame.loadFromFile(file, header.numBones))
            self.frames.append(frame)
        
        # read compressed bone pool
        # see if we reached it yet
        curPos = file.tell()
        if curPos != header.ofsCompBonePool:
            # we're not yet there. If we're off by 0-3 bytes, it's because 32-bit-alignment is forced. Silently seek correct position. Otherwise: warn (and seek correct position, too)
            if curPos > header.ofsCompBonePool or header.ofsCompBonePool > curPos + 3:
                print("Info: Bone Pool in .gla not encountered when expected (at ", file.tell(), " instead of ", header.ofsCompBonePool, "), seeking correct position. There could be a bug in the importer (bad) or the file could be unusual - but not necessarily wrong (no problem).", sep="")
            file.seek(header.ofsCompBonePool)
        # there's one more object than the highest index since those start at 0
        self.bonePool.loadFromFile(file, maxIndex+1)
        
        #file should be over now, bone pool is usually the last thing. I'm not sure it has to be, but so far it has always been.
        if file.tell() != header.ofsEnd:
            print("Info: .gla Bone Pool read but file not over yet - this likely indicates a problem.")
        return True, ""
    
    def saveToFile(self, file):
        for frame in self.frames:
            frame.writeToFile(file)
        self.bonePool.writeToFile()
        pass
    
    def saveToBlender(self, skeleton, armature):
        pass

class GLA:
    
    def __init__(self):
        #whether this is the automatic default skeleton
        self.isDefault = False
        self.header = MdxaHeader()
        self.boneOffsets = MdxaBoneOffsets()
        self.skeleton = MdxaSkel()
        self.boneIndexByName = {}
        # boneNameByIndex = {} #just use bones[index].name
        # the Blender Armature / Object
        self.skeleton_armature = None
        self.skeleton_object = None
        self.animation = MdxaAnimation()
    
    def loadFromFile(self, filepath_abs, loadAnimation):
        try:
            file = open(filepath_abs, mode="rb")
        except IOError:
            print("Could not open file: ", filepath_abs, sep="")
            return False, "Could not open file!"
        # load header
        success, message = self.header.loadFromFile(file)
        if not success:
            return False, message
        # load offsets (directly after header, always)
        self.boneOffsets.loadFromFile(file, self.header.numBones)
        # load bones
        self.skeleton.loadFromFile(file, self.boneOffsets)
        # build lookup map
        for bone in self.skeleton.bones:
            self.boneIndexByName[bone.name] = bone.index
        #todo: load animations
        if loadAnimation:
            success, message = self.animation.loadFromFile(file, self.header, self.skeleton)
            if not success:
                return False, message
        return True, ""
    
    def loadFromBlender(self, gla_filepath_rel):
        #todo
        return True, ""
    
    def saveToFile(self, filepath_abs):
        #todo
        return True, ""
    
    def saveToBlender(self, scene_root, useAnimation, skeletonFixes):
        #default skeleton = no skeleton.
        if self.isDefault:
            return True, ""
        
        #  try using existing skeletons
        # first check if there's already an armature object called skeleton_root. Try using that.
        if "skeleton_root" in bpy.data.objects:
            print("Found a skeleton_root object, trying to use it.")
            self.skeleton_object = bpy.data.objects["skeleton_root"]
            if self.skeleton_object.type != 'ARMATURE':
                return False, "Existing skeleton_root object is no armature!"
            self.skeleton_armature = self.skeleton_object.data
        # If there's no skeleton, there may yet still be an armature. Use that.
        elif "skeleton_root" in bpy.data.armatures:
            print("Found skeleton_root armature, trying to use it.")
            self.skeleton_armature = bpy.data.armatures["skeleton_root"]
        
        # if we found an existing armature, we need to make sure it's linked to an object and valid
        if self.skeleton_armature:
            # see if the armature fits
            success, message =  self.skeleton.fitsArmature(self.skeleton_armature)
            if not success:
                return False, message
            
            # this armature would work, add it to an object if necessary
            if not self.skeleton_object:
                self.skeleton_object = bpy.data.objects.new("skeleton_root", self.skeleton_armature)
            
            # link the object to the current scene if necessary
            if not self.skeleton_object.name in bpy.context.scene.objects:
                bpy.context.scene.objects.link(self.skeleton_object)
            
            # set its parent to the scene_root (not strictly speaking necessary but keeps output consistent)
            self.skeleton_object.parent = scene_root
            
            # add animations, if any
            if useAnimation:
                self.animation.saveToBlender(self.skeleton, self.skeleton_armature)
            
            #that's all
            return True, ""
        
        
        # no existing Armature found, create a new one.
        
        #create armature
        success, message = self.skeleton.saveToBlender(scene_root, skeletonFixes)
        if not success:
            return False, message
        self.skeleton_armature = self.skeleton.armature
        self.skeleton_object = self.skeleton.armature_object
        
        #add animations, if any
        if useAnimation:
            self.animation.saveToBlender(self.skeleton, self.skeleton_armature)
        return True, ""
