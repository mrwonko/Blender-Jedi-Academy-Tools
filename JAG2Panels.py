import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, PointerProperty


# -------------------------------------------------------------
#   PROPERTY GROUP
# -------------------------------------------------------------
class G2Props(bpy.types.PropertyGroup):
    name: StringProperty(
        name="Name",
        maxlen=64,
        default="",
        description="Ghoul2 surface or tag name"
    )

    shader: StringProperty(
        name="Shader",
        maxlen=64,
        default="",
        description="Shader assigned to this surface"
    )

    tag: BoolProperty(
        name="Tag",
        default=False,
        description="Marks object as a Ghoul2 tag"
    )

    off: BoolProperty(
        name="Off",
        default=False,
        description="Surface initially disabled"
    )

    scale: FloatProperty(
        name="Scale",
        default=100.0,
        min=0.0,
        subtype='PERCENTAGE',
        description="Skeleton scale (armature only)"
    )


# -------------------------------------------------------------
#   PROPERTY CHECK HELPERS
# -------------------------------------------------------------
def hasG2MeshProperties(obj):
    return hasattr(obj, "g2_prop") and obj.g2_prop is not None


def initSequenceProperties() -> None:
    # TODO probably handle these custom properties more like the G2Props?
    bpy.types.Action.loop_frame = bpy.props.BoolProperty(
        name="Loop", default=False, description="Whether this squence will loop")
    bpy.types.Action.fps = bpy.props.IntProperty(
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
        return obj and obj.type in {"MESH", "ARMATURE"}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if not hasattr(obj, "g2_prop"):
            layout.label(text="No G2 props found.")
            return

        props = obj.g2_prop

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
    def poll(self, context):
        return context.active_nla_strip and context.active_nla_strip.action is not None
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        row = layout.row()
        row.prop(context.active_nla_strip.action, "loop_frame")
        row = layout.row()
        row.prop(context.active_nla_strip.action, "fps")


class G2ActionPropertiesPanel(bpy.types.Panel):
    bl_label = "GLA Animation Properties"
    bl_idname = "ACTION_PT_g2sequence_props"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Action"

    @classmethod
    def poll(self, context):
        return context.active_action is not None
    
    def draw(self, context):
        layout = self.layout
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

    bpy.types.Object.g2_prop = PointerProperty(type=G2Props)
    initSequenceProperties()


def unregister():
    del bpy.types.Object.g2_prop
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
