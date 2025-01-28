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
reload_modules(locals(), __package__, ["JAG2Scene", "JAG2GLA", "JAFilesystem", "JAG2AnimationCFG"], [".JAG2Constants"])  # nopep8

import bpy
from typing import Tuple, cast
from . import JAG2Scene
from . import JAG2GLA
from . import JAFilesystem
from . import JAG2AnimationCFG
from .JAG2Constants import SkeletonFixes
from bpy_extras.io_utils import ImportHelper, ExportHelper


def GetPaths(basepath, filepath) -> Tuple[str, str]:
    if basepath == "":
        basepath, filepath = JAFilesystem.SplitPrefix(filepath)
        filepath = JAFilesystem.RemoveExtension(filepath)
    else:
        filepath = JAFilesystem.RelPathNoExt(filepath, basepath)
    return basepath, filepath


class GLMImport(bpy.types.Operator, ImportHelper): # type: ignore
    '''Import GLM Operator.'''
    bl_idname = "import_scene.glm"
    bl_label = "Import JA Ghoul 2 Model (.glm)"
    bl_description = "Imports a Ghoul 2 model (.glm), looking up the skeleton (and optionally the animation) from the referenced (or optionally a different) .gla file."
    # register is a must-have when using WindowManager.invoke_props_popup
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".glm"
    filter_glob: bpy.props.StringProperty(default="*.glm", options={'HIDDEN'})  # pyright: ignore [reportInvalidTypeForm]

    def skin_list_cb(self, context):
        try:
            filepath =JAFilesystem.PathToFile(self.filepath, "")
        except:
            print("could not find file or folder")
            return []
        skin_files = []

        try:
            skin_files = sorted(f for f in JAFilesystem.FileList(filepath)
                                    if f.endswith(".skin"))
        except Exception as e:
            print("Could not open skin files, error: ", e)

        items = [(
            "GUESS_TEXTURES",
            "Guess textures",
            "Many models try to force you to use the skin. "
            "Enable this to try to circumvent that. "
            "(Usually works well, but skins should be preferred.)")]
        for skin in skin_files:
            if skin.endswith("_default.skin"):
                items.append((skin, skin.split(".")[0], ""))
        items.append((" ", "None", "Use file internal paths. "))
        
        return items + [(skin, skin.split(".")[0], "")
                for skin in skin_files if not skin.endswith("_default.skin")]
    
    # properties
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="The .glm file to import",
        default="")  # pyright: ignore [reportInvalidTypeForm]
    skin: bpy.props.EnumProperty(
        items=skin_list_cb,
        name="Skin",
        default=1, # type: ignore
        description="The skin to load, choose none to use file internal paths"
    ) # pyright: ignore [reportInvalidTypeForm]
    basepath: bpy.props.StringProperty(
        name="Base Path",
        description="The base folder relative to which paths should be interpreted. Leave empty to let the importer guess (needs /GameData/ in filepath).",
        default=""
        )  # pyright: ignore [reportInvalidTypeForm]
    glaOverride: bpy.props.StringProperty(
        name=".gla override",
        description="Gla file to use, relative to base. Leave empty to use the one referenced in the file.",
        maxlen=64,
        default="")  # pyright: ignore [reportInvalidTypeForm]
    scale: bpy.props.FloatProperty(
        name="Scale",
        description="Scale to apply to the imported model.",
        default=10,
        min=0,
        max=1000,
        subtype='PERCENTAGE')  # pyright: ignore [reportInvalidTypeForm]
    skeletonFixes: bpy.props.EnumProperty(
        name="skeleton changes",
        description="You can select a preset for automatic skeleton changes which result in a nicer imported skeleton.",
        default='NONE',
        items=[
        (SkeletonFixes.NONE.value, "None", "Don't change the skeleton in any way.", 0),
        (SkeletonFixes.JKA_HUMANOID.value, "Jedi Academy _humanoid",
         "Fixes for the default humanoid Jedi Academy skeleton", 1)
    ])  # pyright: ignore [reportInvalidTypeForm, reportArgumentType]
    loadAnimations: bpy.props.EnumProperty(
        name="animations",
        description="Whether to import all animations, some animations or only a range from the .gla. (Importing huge animations takes forever.)",
        default='NONE',
        items=[
        (JAG2GLA.AnimationLoadMode.NONE.value, "None", "Don't import animations.", 0),
        (JAG2GLA.AnimationLoadMode.CFG.value, "Cfg", "Import animations from animations.cfg file", 1),
        (JAG2GLA.AnimationLoadMode.ALL.value, "All (slow)", "Import all animations", 2),
        (JAG2GLA.AnimationLoadMode.RANGE.value, "Range (slow)", "Import a certain range of frames", 3)
    ])  # pyright: ignore [reportInvalidTypeForm, reportArgumentType]
    startFrame: bpy.props.IntProperty(
        name="Start frame",
        description="If only a range of frames of the animation is to be imported, this is the first.",
        default=0,
        min=0)  # pyright: ignore [reportInvalidTypeForm]
    numFrames: bpy.props.IntProperty(
        name="number of frames",
        description="If only a range of frames of the animation is to be imported, this is the total number of frames to import",
        default=1,
        min=1)  # pyright: ignore [reportInvalidTypeForm]

    def execute(self, context):
        print("\n== GLM Import ==\n")
        # initialize paths
        basepath, filepath = GetPaths(self.basepath, self.filepath)
        if self.basepath != "" and JAFilesystem.RemoveExtension(self.filepath) == filepath:
            self.report({'ERROR'}, "Invalid Base Path")
            return {'FINISHED'}
        # de-percentagionise scale
        scale = self.scale / 100
        # load GLM
        scene = JAG2Scene.Scene(basepath)
        success, message = scene.loadFromGLM(filepath)
        if not success:
            self.report({'ERROR'}, message)
            return {'FINISHED'}
        # load GLA - has to be done in any case since that's where the skeleton is stored
        if self.glaOverride == "":
            glafile = scene.getRequestedGLA()
        else:
            glafile = cast(str, self.glaOverride)
        loadAnimations = JAG2GLA.AnimationLoadMode[self.loadAnimations]
        if loadAnimations == JAG2GLA.AnimationLoadMode.CFG:
            cfg_file_path = JAFilesystem.PathToFile(glafile, basepath)
            success, message = scene.loadFromCFG(cfg_file_path)
        if not success:
            self.report({'ERROR'}, message)
            return {'FINISHED'}
        success, message = scene.loadFromGLA(
            glafile, loadAnimations, cast(int, self.startFrame), cast(int, self.numFrames))
        if not success:
            self.report({'ERROR'}, message)
            return {'FINISHED'}
        # output to blender
        skin = ""
        guess_textures = False
        if self.skin == "GUESS_TEXTURES":
            skin = ""
            guess_textures = True
        elif self.skin.strip() != "":
            skin = JAFilesystem.PathToFile(filepath, "")  + self.skin
        success, message = scene.saveToBlender(
            scale,
            skin,
            guess_textures,
            loadAnimations != JAG2GLA.AnimationLoadMode.NONE,
            SkeletonFixes[self.skeletonFixes])
        if not success:
            self.report({'ERROR'}, message)
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        row = layout.row()
        row.prop(self, "skin")
        row = layout.row()
        row.prop(self, "basepath")
        row = layout.row()
        row.prop(self, "glaOverride")
        row = layout.row()
        row.prop(self, "scale")
        row = layout.row()
        row.prop(self, "skeletonFixes")
        row = layout.row()
        row.prop(self, "loadAnimations")
        if self.loadAnimations == JAG2GLA.AnimationLoadMode.RANGE.value:
            row = layout.row()
            row.prop(self, "startFrame")
            row = layout.row()
            row.prop(self, "numFrames")

    def invoke(self, context, event): # type: ignore
        prefs = bpy.context.preferences.addons[__name__.split('.')[0]].preferences
        self.basepath = prefs.base_path
        self.scale = prefs.scale
        return super().invoke(context, event)


class GLAImport(bpy.types.Operator, ImportHelper): # type: ignore
    '''Import GLA Operator.'''
    bl_idname = "import_scene.gla"
    bl_label = "Import JA Ghoul 2 Skeleton (.gla)"
    bl_description = "Imports a Ghoul 2 skeleton (.gla) and optionally the animation."
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".gla"  # I believe this limits the shown files.
    filter_glob: bpy.props.StringProperty(default="*.gla", options={'HIDDEN'})  # pyright: ignore [reportInvalidTypeForm]

    # properties
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="The .gla file to import",
        maxlen=1024,
        default="")  # pyright: ignore [reportInvalidTypeForm]
    basepath: bpy.props.StringProperty(
        name="Base Path",
        description="The base folder relative to which paths should be interpreted. Leave empty to let the importer guess (needs /GameData/ in filepath).",
        default="")  # pyright: ignore [reportInvalidTypeForm]
    scale: bpy.props.FloatProperty(
        name="Scale",
        description="Scale to apply to the imported model.",
        default=10,
        min=0, 
        max=1000,
        subtype='PERCENTAGE')  # pyright: ignore [reportInvalidTypeForm]
    skeletonFixes: bpy.props.EnumProperty(
        name="skeleton changes",
        description="You can select a preset for automatic skeleton changes which result in a nicer imported skeleton.",
        default='NONE', items=[
        (SkeletonFixes.NONE.value, "None", "Don't change the skeleton in any way.", 0),
        (SkeletonFixes.JKA_HUMANOID.value, "Jedi Academy _humanoid",
         "Fixes for the default humanoid Jedi Academy skeleton", 1)
    ])  # pyright: ignore [reportInvalidTypeForm, reportArgumentType]
    loadAnimations: bpy.props.EnumProperty(
        name="animations",
        description="Whether to import all animations, some animations or only a range from the .gla. (Importing huge animations takes forever.)",
        default='NONE',
        items=[
        (JAG2GLA.AnimationLoadMode.NONE.value, "None", "Don't import animations.", 0),
        (JAG2GLA.AnimationLoadMode.CFG.value, "Cfg", "Import animations from animations.cfg file", 1),
        (JAG2GLA.AnimationLoadMode.ALL.value, "All (slow)", "Import all animations", 2),
        (JAG2GLA.AnimationLoadMode.RANGE.value, "Range (slow)", "Import a certain range of frames", 3)
    ])  # pyright: ignore [reportInvalidTypeForm, reportArgumentType]
    startFrame: bpy.props.IntProperty(
        name="Start frame",
        description="If only a range of frames of the animation is to be imported, this is the first.",
        default=0,
        min=0)  # pyright: ignore [reportInvalidTypeForm]
    numFrames: bpy.props.IntProperty(
        name="number of frames",
        description="If only a range of frames of the animation is to be imported, this is the total number of frames to import",
        default=1,
        min=1)  # pyright: ignore [reportInvalidTypeForm]

    def execute(self, context):
        print("\n== GLA Import ==\n")
        # de-percentagionise scale
        scale = self.scale / 100
        # initialize paths
        basepath, filepath = GetPaths(self.basepath, self.filepath)
        if self.basepath != "" and JAFilesystem.RemoveExtension(self.filepath) == filepath:
            self.report({'ERROR'}, "Invalid Base Path")
            return {'FINISHED'}
        # load GLA
        scene = JAG2Scene.Scene(basepath)
        loadAnimations = JAG2GLA.AnimationLoadMode[self.loadAnimations]
        success = True
        message = "Nothing"
        if loadAnimations == JAG2GLA.AnimationLoadMode.CFG:
            cfg_file_path = JAFilesystem.PathToFile(filepath, basepath)
            success, message = scene.loadFromCFG(cfg_file_path)
        if not success:
            self.report({'ERROR'}, message)
            return {'FINISHED'}
        success, message = scene.loadFromGLA(
            filepath, loadAnimations, self.startFrame, self.numFrames)
        if not success:
            self.report({'ERROR'}, message)
            return {'FINISHED'}
        # output to blender
        success, message = scene.saveToBlender(
            scale, "", False, loadAnimations != JAG2GLA.AnimationLoadMode.NONE, SkeletonFixes[self.skeletonFixes])
        if not success:
            self.report({'ERROR'}, message)
        return {'FINISHED'}
    
    def invoke(self, context, event): # type: ignore
        prefs = bpy.context.preferences.addons[__name__.split('.')[0]].preferences
        self.basepath = prefs.base_path
        self.scale = prefs.scale
        return super().invoke(context, event)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        row = layout.row()
        row.prop(self, "basepath")
        row = layout.row()
        row.prop(self, "scale")
        row = layout.row()
        row.prop(self, "skeletonFixes")
        row = layout.row()
        row.prop(self, "loadAnimations")
        if self.loadAnimations == JAG2GLA.AnimationLoadMode.RANGE.value:
            row = layout.row()
            row.prop(self, "startFrame")
            row = layout.row()
            row.prop(self, "numFrames")


class GLMExport(bpy.types.Operator, ExportHelper): # type: ignore
    '''Export GLM Operator.'''
    bl_idname = "export_scene.glm"
    bl_label = "Export JA Ghoul 2 Model (.glm)"
    bl_description = "Exports a Ghoul 2 model (.glm)"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".glm"
    filter_glob: bpy.props.StringProperty(default="*.glm", options={'HIDDEN'})  # pyright: ignore [reportInvalidTypeForm]

    # properties
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="The filename to export to",
        maxlen=1024,
        default="")  # pyright: ignore [reportInvalidTypeForm]
    basepath: bpy.props.StringProperty(
        name="Base Path",
        description="The base folder relative to which paths should be interpreted. Leave empty to let the exporter guess (needs /GameData/ in filepath).",
        default="")  # pyright: ignore [reportInvalidTypeForm]
    gla: bpy.props.StringProperty(
        name=".gla name", description="Name of the skeleton this model uses (must exist!)", default="models/players/_humanoid/_humanoid")  # pyright: ignore [reportInvalidTypeForm]

    def execute(self, context):
        print("\n== GLM Export ==\n")
        # initialize paths
        basepath, filepath = GetPaths(self.basepath, self.filepath)
        if self.basepath != "" and JAFilesystem.RemoveExtension(self.filepath) == filepath:
            self.report({'ERROR'}, "Invalid Base Path")
            return {'FINISHED'}
        # try to load from Blender's data to my intermediate format
        scene = JAG2Scene.Scene(basepath)
        success, message = scene.loadModelFromBlender(filepath, self.gla)
        if not success:
            self.report({'ERROR'}, message)
            return {'FINISHED'}
        # try to save
        success, message = scene.saveToGLM(filepath)
        if not success:
            self.report({'ERROR'}, message)
        return {'FINISHED'}
    
    def invoke(self, context, event): # type: ignore
        prefs = bpy.context.preferences.addons[__name__.split('.')[0]].preferences
        self.basepath = prefs.base_path
        return super().invoke(context, event)


class GLAExport(bpy.types.Operator, ExportHelper): # type: ignore
    '''Export GLA Operator.'''
    bl_idname = "export_scene.gla"
    bl_label = "Export JA Ghoul 2 Skeleton & Animation (.gla)"
    bl_description = "Exports a Ghoul 2 Skeleton and its animations (.gla)"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".gla"
    filter_glob: bpy.props.StringProperty(default="*.gla", options={'HIDDEN'})  # pyright: ignore [reportInvalidTypeForm]

    # properties
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="The filename to export to",
        maxlen=1024,
        default="")  # pyright: ignore [reportInvalidTypeForm]
    basepath: bpy.props.StringProperty(
        name="Base Path",
        description="The base folder relative to which paths should be interpreted. Leave empty to let the exporter guess (needs /GameData/ in filepath).",
        default="")  # pyright: ignore [reportInvalidTypeForm]
    glapath: bpy.props.StringProperty(
        name="gla name",
        description="The relative path of this gla. Leave empty to let the exporter guess (needs /GameData/ in filepath).",
        maxlen=64,
        default="")  # pyright: ignore [reportInvalidTypeForm]
    glareference: bpy.props.StringProperty(
        name="gla reference",
        description="Copies the bone indices from this skeleton, if any (e.g. for new animations for existing skeleton; path relative to the Base Path)",
        maxlen=64,
        default="")  # pyright: ignore [reportInvalidTypeForm]

    def execute(self, context):
        print("\n== GLA Export ==\n")
        # initialize paths
        basepath, filepath = GetPaths(self.basepath, self.filepath)
        print("Basepath: {}\tFilename: {}".format(
            basepath, filepath))  # todo delete!!!!!
        glapath = filepath
        if self.glapath != "":
            glapath = self.glapath
        glapath = glapath.replace("\\", "/")
        if self.basepath != "" and JAFilesystem.RemoveExtension(self.filepath) == filepath:
            self.report({'ERROR'}, "Invalid Base Path")
            return {'FINISHED'}
        # try to load from Blender's data to my intermediate format
        scene = JAG2Scene.Scene(basepath)
        success, message = scene.loadSkeletonFromBlender(
            glapath, self.glareference)
        if not success:
            self.report({'ERROR'}, message)
            return {'FINISHED'}
        # try to save
        success, message = scene.saveToGLA(filepath)
        if not success:
            self.report({'ERROR'}, message)
        return {'FINISHED'}
    
    def invoke(self, context, event): # type: ignore
        prefs = bpy.context.preferences.addons[__name__.split('.')[0]].preferences
        self.basepath = prefs.base_path
        return super().invoke(context, event)


class ObjectAddG2Properties(bpy.types.Operator):
    bl_idname = "object.add_g2_properties"
    bl_label = "Add G2 properties"
    bl_description = "Adds Ghoul 2 properties"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type in ['MESH', 'ARMATURE'] or False

    def execute(self, context):
        obj = context.active_object
        if obj.type == 'MESH':
            # don't overwrite those that already exist
            if not "g2_prop_off" in obj:
                obj.g2_prop_off = False  # pyright: ignore [reportAttributeAccessIssue]
            if not "g2_prop_tag" in obj:
                obj.g2_prop_tag = False  # pyright: ignore [reportAttributeAccessIssue]
            if not "g2_prop_name" in obj:
                obj.g2_prop_name = ""  # pyright: ignore [reportAttributeAccessIssue]
            if not "g2_prop_shader" in obj:
                obj.g2_prop_shader = ""  # pyright: ignore [reportAttributeAccessIssue]
        else:
            assert (obj.type == 'ARMATURE')
            if not "g2_prop_scale" in obj:
                obj.g2_prop_scale = 100  # pyright: ignore [reportAttributeAccessIssue]
        return {'FINISHED'}


class ObjectRemoveG2Properties(bpy.types.Operator):
    bl_idname = "object.remove_g2_properties"
    bl_label = "Remove G2 properties"
    bl_description = "Removes Ghoul 2 properties"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type in ['MESH', 'ARMATURE'] or False

    def execute(self, context):
        obj = context.active_object
        if obj.type == 'MESH':
            bpy.types.Object.__delitem__(obj, "g2_prop_off")
            bpy.types.Object.__delitem__(obj, "g2_prop_tag")
            bpy.types.Object.__delitem__(obj, "g2_prop_name")
            bpy.types.Object.__delitem__(obj, "g2_prop_shader")
        else:
            assert (obj.type == 'ARMATURE')
            bpy.types.Object.__delitem__(obj, "g2_prop_scale")
        return {'FINISHED'}


class GLAMetaExport(bpy.types.Operator, ExportHelper): # type: ignore
    '''Export GLA Metadata Operator.'''
    bl_idname = "export_scene.gla_meta"
    bl_label = "Export JA Ghoul 2 Animation metadata (.cfg)"
    bl_description = "Exports timeline markers labelling the animations to a .cfg file"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".cfg"
    filter_glob: bpy.props.StringProperty(default="*.cfg", options={'HIDDEN'}) # pyright: ignore [reportInvalidTypeForm]

    # properties
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="The filename to export to",
        maxlen=1024,
        default="")  # pyright: ignore [reportInvalidTypeForm]
    source: bpy.props.EnumProperty(
        name="source",
        description="Source for creating the animation frames",
        default='NLA',
        items=[
        ("NLA", "NLA Strips", "Get all info from the NLA strips.", 0),
        ("MARKERS", "Frame Markers", "Get all info from named timeline markers.", 1)
    ])  # pyright: ignore [reportInvalidTypeForm, reportArgumentType]
    offset: bpy.props.IntProperty(
        name="Offset",
        description="Frame offset for the animations, e.g. 21376 if you plan on merging with Jedi Academy's _humanoid.gla",
        min=0,
        default=0)  # pyright: ignore [reportInvalidTypeForm]

    def execute(self, context):
        print("\n== GLA Metadata Export ==\n")

        export_cfg = JAG2AnimationCFG.AnimationCGF()
        if self.source == "NLA":
            success, message = export_cfg.from_blender_nla_tracks(context, self.offset)
        else:
            success, message = export_cfg.from_blender_markers(context, self.offset)
        if not success:
            self.report({'ERROR'}, message)
            return {'FINISHED'}
        
        with open(self.filepath, "w") as file:
            file.write("// Animation Data generated from Blender Markers\n")
            file.write("// name\t\tstart\tlength\tloop\tfps\n")
            file.write(str(export_cfg))

        return {'FINISHED'}


# menu button callback functions


def menu_func_export_glm(self, context):
    self.layout.operator(GLMExport.bl_idname, text="JA Ghoul 2 model (.glm)")


def menu_func_export_gla(self, context):
    self.layout.operator(GLAExport.bl_idname,
                         text="JA Ghoul 2 skeleton/animation (.gla)")


def menu_func_export_gla_meta(self, context):
    self.layout.operator(GLAMetaExport.bl_idname,
                         text="JA Ghoul 2 animation markers (.cfg)")


def menu_func_import_glm(self, context):
    self.layout.operator(GLMImport.bl_idname, text="JA Ghoul 2 model (.glm)")


def menu_func_import_gla(self, context):
    self.layout.operator(GLAImport.bl_idname,
                         text="JA Ghoul 2 skeleton/animation (.gla)")

# menu button init/destroy


def register():
    bpy.utils.register_class(GLMExport)
    bpy.utils.register_class(GLAExport)
    bpy.utils.register_class(GLAMetaExport)
    bpy.utils.register_class(GLMImport)
    bpy.utils.register_class(GLAImport)

    bpy.utils.register_class(ObjectAddG2Properties)
    bpy.utils.register_class(ObjectRemoveG2Properties)

    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_glm)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_gla)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_gla_meta)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_glm)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_gla)


def unregister():
    bpy.utils.unregister_class(GLMExport)
    bpy.utils.unregister_class(GLAExport)
    bpy.utils.unregister_class(GLAMetaExport)
    bpy.utils.unregister_class(GLMImport)
    bpy.utils.unregister_class(GLAImport)

    bpy.utils.unregister_class(ObjectAddG2Properties)
    bpy.utils.unregister_class(ObjectRemoveG2Properties)

    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_glm)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_gla)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_gla_meta)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_glm)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_gla)
