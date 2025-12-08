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
    return hasattr(obj, "g2_props") and obj.g2_props is not None


def hasG2ArmatureProperties(obj):
    return hasattr(obj, "g2_props") and obj.g2_props is not None


# -------------------------------------------------------------
#   UI PANEL
# -------------------------------------------------------------
class G2PropertiesPanel(bpy.types.Panel):
    bl_label = "Ghoul 2 Properties"
    bl_idname = "OBJECT_PT_g2_props"
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

        if not hasattr(obj, "g2_props"):
            layout.label(text="No G2 props found.")
            return

        props = obj.g2_props

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


# -------------------------------------------------------------
#   OPERATORS
# -------------------------------------------------------------
class OBJECT_OT_AddG2Properties(bpy.types.Operator):
    bl_idname = "object.add_g2_properties"
    bl_label = "Add Ghoul 2 Properties"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        obj = context.active_object
        _ = obj.g2_props   # ensures existence
        self.report({'INFO'}, f"Added G2 properties to {obj.name}")
        return {'FINISHED'}


class OBJECT_OT_RemoveG2Properties(bpy.types.Operator):
    bl_idname = "object.remove_g2_properties"
    bl_label = "Remove Ghoul 2 Properties"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        obj = context.active_object
        props = obj.g2_props

        props.name = ""
        props.shader = ""
        props.tag = False
        props.off = False
        props.scale = 100

        self.report({'INFO'}, f"Reset G2 properties for {obj.name}")
        return {'FINISHED'}


# -------------------------------------------------------------
#   REGISTRATION
# -------------------------------------------------------------
classes = (
    G2Props,
    G2PropertiesPanel,
    OBJECT_OT_AddG2Properties,
    OBJECT_OT_RemoveG2Properties,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.g2_props = PointerProperty(type=G2Props)


def unregister():
    del bpy.types.Object.g2_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
