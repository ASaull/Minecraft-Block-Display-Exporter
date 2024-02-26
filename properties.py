from bpy.types import PropertyGroup, PropertyGroup, Scene, Object
from bpy.props import (
    StringProperty,
    PointerProperty,
)
from . import block_definitions
from . import properties_util


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
    
    def get_variants(self, context, edit_text):
        return []

    block_type: StringProperty(
        name="Block Type",
        default="stone",
        description="The type of Minecraft block associated with this mesh",
        update=properties_util.change_block_type,
        search=get_block_list
    )
    block_variant: StringProperty(
        name="Block Variant",
        default="{}",
        description="The variations associated with the Minecraft block",
        update=properties_util.change_block_type,
        search=get_variants
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


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)

    del Object.mcbde
    del Scene.mcbde