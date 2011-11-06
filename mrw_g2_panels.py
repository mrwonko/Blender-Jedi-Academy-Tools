import bpy

def hasG2Properties(obj):
    """ Whether a given object has the ghoul 2 properties """
    return ("g2_prop_off" in obj) and ("g2_prop_tag" in obj) and ("g2_prop_name" in obj)

def initG2Properties():
    """ globally initializes the ghoul 2 custom properties """
    bpy.types.Object.g2_prop_name = bpy.props.StringProperty(name="name", maxlen=64, default="", description="Name (in case it doesn't fit in Blender's Object Name, which is used if this is empty.)")
    bpy.types.Object.g2_prop_tag = bpy.props.BoolProperty(name="Tag", default=False, description="Whether this object represents a tag.")
    bpy.types.Object.g2_prop_off = bpy.props.BoolProperty(name="Off", default=False, description="Whether this object should be initially off (can be overridden in skin).")

class G2PropertiesPanel(bpy.types.Panel):
    bl_label = "Ghoul 2 Properties"
    bl_idname = "OBJECT_PT_g2_props"
    bl_space_type = 'PROPERTIES' # goes in the properties editor
    bl_region_type = 'WINDOW'
    bl_context = "object" # in the objects tab

    def draw(self, context):
        layout = self.layout

        obj = context.object
        
        if hasG2Properties(obj):
            row = layout.row()
            row.operator("object.remove_g2_properties")
            
            row = layout.row()
            row.prop(obj, "g2_prop_name")
            
            row = layout.row()
            row.prop(obj, "g2_prop_tag")
            row.prop(obj, "g2_prop_off")
        else:
            row = layout.row()
            row.operator("object.add_g2_properties")