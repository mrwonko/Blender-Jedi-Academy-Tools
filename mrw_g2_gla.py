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
        self.scale, self.numFrames, self.numBones, self.numBones, self.ofsCompBonePool, self.ofsSkel, self.ofsEnd = struct.unpack("f6i", file.read(7*4))
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
    
    # changes the hierarchy as defined for this fix
    def applySkeletonFixes(self, skeletonFixes, bones):
        parentChanges = mrw_g2_constants.PARENT_CHANGES[skeletonFixes]
        # if this bone's parent changes:
        if self.index in parentChanges:
            assert(self.parent != -1) #I don't think I ever need to change from no parent to some parent, so I keep the code simple through this assertion.
            
            # remove it from the old parent
            oldParent = bones[self.parent]
            oldParent.children.remove(self.index)
            oldParent.numChildren -= 1
            
            # change its parent
            self.parent = parentChanges[self.index]
            
            # and add it to the new one
            newParent = bones[self.parent]
            newParent.numChildren += 1
            newParent.children.append(self.index)
    
    #blenderBonesSoFar is a dictionary of boneIndex -> BlenderBone
    #allBones is the list of all MdxaBones
    #use it to set up hierarchy and add yourself once done.
    def toBlender(self, armature, blenderBonesSoFar, allBones, skeletonFixes):
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
        
        # set parent, if any
        if self.parent != -1:
            mdxaParent = allBones[self.parent]
            blenderParent = blenderBonesSoFar[self.parent]
            bone.parent = blenderParent
            # if this is the only child of its parent or has priority: Connect the parent to this.
            # I'd like it unconnected right now.
            if False:
            #if mdxaParent.numChildren == 1 or self.name in mrw_g2_constants.PRIORITY_BONES[skeletonFixes]:
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
    
    def loadFromFile(self, file, offsets, skeletonFixes):
        for i, offset in enumerate(offsets.boneOffsets):
            file.seek(offsets.baseOffset + offset)
            bone = MdxaBone()
            bone.loadFromFile(file)
            bone.index = i
            self.bones.append(bone)
        # apply the skeleton fixes - bones need to be completely loaded first
        for bone in self.bones:
            bone.applySkeletonFixes(skeletonFixes, self.bones)
    
    def fitsArmature(self, armature):
        for bone in self.bones:
            if not bone.name in armature.bones:
                return False, "Bone "+bone.name+" not found in existing skeleton_root armature!"
            return True, ""
    
    def toBlender(self, scene_root, skeletonFixes):
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
        # already created blender bone objects by index
        createdBones = {}
        # bones yet to be created
        uncreatedBones = []
        uncreatedBones.extend(self.bones)
        while len(uncreatedBones) > 0:
            # whether a new bone was created this time - if not, there's a hierarchy problem
            createdBone = False
            newUncreatedBones = []
            for bone in uncreatedBones:
                # only create those bones whose parent has already been created.
                if bone.parent in createdBonesIndices:
                    bone.toBlender(self.armature, createdBones, self.bones, skeletonFixes)
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
    
    def loadFromFile(self, filepath_abs, skeletonFixes):
        self.skeletonFixes = skeletonFixes
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
        self.skeleton.loadFromFile(file, self.boneOffsets, skeletonFixes)
        # build lookup map
        for bone in self.skeleton.bones:
            self.boneIndexByName[bone.name] = bone.index
        #todo: load animations
        return True, ""
    
    def loadFromBlender(self, gla_filepath_rel):
        #todo
        return True, ""
    
    def saveToFile(self, filepath_abs):
        #todo
        return True, ""
    
    def saveToBlender(self, scene_root,):
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
            
            #that's all
            return True, ""
        
        
        # no existing Armature found, create a new one.
        
        #create armature
        success, message = self.skeleton.toBlender(scene_root, self.skeletonFixes)
        if not success:
            return False, message
        self.skeleton_armature = self.skeleton.armature
        self.skeleton_object = self.skeleton.armature_object
        
        #todo: animate
        return True, ""
