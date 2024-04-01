from bpy.types import Panel, Object
from .data_loader import data_loader
import bpy

class McbdePanel(Panel):
    """
    Panel for the MCBDE addon.
    """
    bl_idname = "MCBDE_Panel"
    bl_label = "MCBDE"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MCBDE"
    bl_options = {'HEADER_LAYOUT_EXPAND'}


    def draw(self, context):
        layout = self.layout
        active_object = context.active_object

        # Data section
        layout.label(text="Minecraft Data:")
        layout.prop(context.scene.mcbde, "minecraft_location")
        layout.operator("object.load_data_button")

        if not data_loader.is_initialized():
            return

        # Selection section
        layout.label(text="Selected Blocks:")
        col = layout.column()

        if active_object and active_object.type == 'MESH' and active_object.mcbde:
            col.prop(active_object.mcbde, "block_type")
            #col.prop(active_object.mcbde, "block_variant")

            # Adding the block properties
            if "block_properties" in active_object.mcbde:
                for property in active_object.mcbde.block_properties:
                    row = layout.row()
                    row.label(text=property.name)
                    row.prop(property, "value")
        else:
            layout.label(text="Select a mesh object with MCBDE properties.")

        # Generation section
        layout.label(text="Generation:")
        col = layout.column()

        col.operator("object.generate_button")
        layout.prop(context.scene.mcbde, "command")


classes = (
    McbdePanel,
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
