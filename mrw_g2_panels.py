import bpy


class G2PropertiesPanel(bpy.types.Panel):
    bl_label = "Ghoul 2 Properties"
    bl_idname = "OBJECT_PT_g2_props"
    bl_space_type = "PROPERTIES" # goes in the properties editor
    bl_region_type = "WINDOW"
    bl_context = "object" # in the objects tab

    def draw(self, context):
        layout = self.layout

        obj = context.object

        row = layout.row()
        row.label(text="Hello world!", icon='WORLD_DATA')

        #todo
        row = layout.row()
        row.label(text="Active object is: " + obj.name)
        row = layout.row()
        if "longName" in obj:
            row.label(text="Name")
            row.prop(obj, "longName")
        else:
            row.label(text='longName goes here')