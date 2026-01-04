from .mod_reload import reload_modules
reload_modules(locals(), __package__, [], [".casts"])  # nopep8

import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, PointerProperty

from .casts import optional_cast


# -------------------------------------------------------------
#   PROPERTY GROUP
# -------------------------------------------------------------
class G2Props(bpy.types.PropertyGroup):
    name: StringProperty(
        name="Name",
        maxlen=64,
        default="",
        description="Ghoul2 surface or tag name"
    )  # type: ignore

    shader: StringProperty(
        name="Shader",
        maxlen=64,
        default="",
        description="Shader assigned to this surface"
    )  # type: ignore

    tag: BoolProperty(
        name="Tag",
        default=False,
        description="Marks object as a Ghoul2 tag"
    )  # type: ignore

    off: BoolProperty(
        name="Off",
        default=False,
        description="Surface initially disabled"
    )  # type: ignore

    scale: FloatProperty(
        name="Scale",
        default=100.0,
        min=0.0,
        subtype='PERCENTAGE',
        description="Skeleton scale (armature only)"
    )  # type: ignore


# -------------------------------------------------------------
#   PROPERTY CHECK HELPERS
# -------------------------------------------------------------
def hasG2MeshProperties(obj):
    return hasattr(obj, "g2_prop") and obj.g2_prop is not None


def initSequenceProperties() -> None:
    # TODO probably handle these custom properties more like the G2Props?
    bpy.types.Action.loop_frame = bpy.props.BoolProperty(  # pyright: ignore[reportAttributeAccessIssue]
        name="Loop", default=False, description="Whether this squence will loop")
    bpy.types.Action.fps = bpy.props.IntProperty(  # pyright: ignore[reportAttributeAccessIssue]
        name="FPS", default=30, description="Sequence playback fps")


def hasG2ArmatureProperties(obj):
    return hasattr(obj, "g2_prop") and obj.g2_prop is not None


# -------------------------------------------------------------
#   UI PANELS
# -------------------------------------------------------------
class G2PropertiesPanel(bpy.types.Panel):
    bl_label = "Ghoul 2 Properties"
    bl_idname = "OBJECT_PT_g2_prop"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type in {"MESH", "ARMATURE"}

    def draw(self, context):
        if (layout := self.layout) is None:
            return
        obj = optional_cast(bpy.types.Object, context.active_object)

        if not hasattr(obj, "g2_prop"):
            layout.label(text="No G2 props found.")
            return

        props = obj.g2_prop  # pyright: ignore[reportAttributeAccessIssue]

        if obj.type == "MESH":
            layout.operator("object.remove_g2_properties")
            layout.prop(props, "name")
            layout.prop(props, "shader")

            row = layout.row()
            row.prop(props, "tag")
            row.prop(props, "off")

        elif obj.type == "ARMATURE":
            layout.operator("object.remove_g2_properties")
            layout.prop(props, "scale")


class G2NLAPropertiesPanel(bpy.types.Panel):
    bl_label = "GLA Animation Properties"
    bl_idname = "STRIP_PT_g2sequence_props"
    bl_space_type = 'NLA_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        return context.active_nla_strip is not None and context.active_nla_strip.action is not None

    def draw(self, context):
        if (layout := self.layout) is None:
            return
        # draw() is only called when poll() returns True, so we can assume this is not None
        action = optional_cast(bpy.types.Action, optional_cast(bpy.types.NlaStrip, context.active_nla_strip).action)
        layout.use_property_split = True
        row = layout.row()
        row.prop(action, "loop_frame")
        row = layout.row()
        row.prop(action, "fps")


class G2ActionPropertiesPanel(bpy.types.Panel):
    bl_label = "GLA Animation Properties"
    bl_idname = "ACTION_PT_g2sequence_props"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Action"

    @classmethod
    def poll(cls, context):
        return context.active_action is not None

    def draw(self, context):
        if (layout := self.layout) is None:
            return
        layout.use_property_split = True
        row = layout.row()
        row.prop(context.active_action, "loop_frame")
        row = layout.row()
        row.prop(context.active_action, "fps")


# -------------------------------------------------------------
#   REGISTRATION
# -------------------------------------------------------------
classes = (
    G2Props,
    G2PropertiesPanel,
    G2NLAPropertiesPanel,
    G2ActionPropertiesPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.g2_prop = PointerProperty(type=G2Props)  # pyright: ignore[reportAttributeAccessIssue]
    initSequenceProperties()


def unregister():
    del bpy.types.Object.g2_prop  # pyright: ignore[reportAttributeAccessIssue]
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
