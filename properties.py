from bpy.types import PropertyGroup, PropertyGroup, Scene, Object
from bpy.props import (
    EnumProperty,
    StringProperty,
    PointerProperty,
)
from . import block_definitions
        

def change_block_type(self, context):
    """
    Change the block type for selected objects.
    """
    print(self["block_type"])
    for obj in context.selected_objects:
        obj.mcbde["block_type"] = self["block_type"]
    print("Changing material for " + context.active_object.name + " to " + self.block_type)


class McbdeMenuProperties(PropertyGroup):
    """
    Properties for the MCBDE menu.
    """

    command: StringProperty(
        name="Command",
        description="Copy this into your Command Block in Minecraft",
        default="",
        maxlen=2048,
        options={'HIDDEN', 'SKIP_SAVE'}
    )


class McbdeBlockProperties(PropertyGroup):
    """
    Properties for Blender objects which represent Minecraft Blocks
    """

    def get_block_list(self, context, edit_text):
        return [item[0] for item in block_definitions.blocks]


    block_type: StringProperty(
        name="Block Type",
        default="stone",
        description="The type of Minecraft block associated with this mesh",
        update=change_block_type,
        search=get_block_list
    )


classes = (
    McbdeMenuProperties,
    McbdeBlockProperties,
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    Object.mcbde = PointerProperty(type=McbdeBlockProperties)
    Scene.mcbde = PointerProperty(type=McbdeMenuProperties)

    #populate_block_collection()

    print("set object and scene mcbde")


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)

    del Object.mcbde
    del Scene.mcbde