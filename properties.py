from bpy.types import PropertyGroup, PropertyGroup, Scene, Object
from bpy.props import (
    StringProperty,
    PointerProperty,
    CollectionProperty,
    EnumProperty
)
import json
from . import block_definitions
from . import properties_util
from .data_loader import data_loader


class BlockProperty(PropertyGroup):
    """
    Class representing a single block property.
    Used to populate the block_properties collection.
    value_options is a string because Blender are immutable

    Example usage:
    name: facing
    value: east
    value_options: ["east", "west", "north", "south"]
    """
    
    def get_items(self, context, edit_text):
        return json.loads(self.value_options)

    value: StringProperty(
        name="",
        default="",
        search=get_items,
        update=properties_util.change_block_variant
    ) # type: ignore
    value_options: StringProperty() # type: ignore


class McbdeMenuProperties(PropertyGroup):
    """
    Properties for the MCBDE menu.
    """

    minecraft_location: StringProperty(
        name="Minecraft Location",
        description='The .jar file for the desired Minecraft version. Will be found in ".minecraft/versions/VERSION/VERSION.jar"',
        default="",
        subtype = 'FILE_PATH'
    ) # type: ignore
    command: StringProperty(
        name="Command",
        description="Copy this into your Command Block in Minecraft",
        default="",
        maxlen=0,
        options={'HIDDEN', 'SKIP_SAVE'}
    ) # type: ignore


class McbdeBlockData(PropertyGroup):
    """
    Properties for Blender objects which represent Minecraft Blocks
    """

    def get_block_list(self, context, edit_text):
        return [item[0] for item in block_definitions.blocks]
    
    def get_variants(self, context, edit_text):
        blockstate = data_loader.get_data("blockstates", self.block_type)
        return blockstate["variants"]

    block_type: StringProperty(
        name="Type",
        default="",
        description="The type of Minecraft block associated with this mesh",
        update=properties_util.change_block_type,
        search=get_block_list
    ) # type: ignore
    block_variant: StringProperty(
        name="Variant",
        default="{}",
        description="The variations associated with the Minecraft block",
        update=properties_util.change_block_variant,
        search=get_variants
    ) # type: ignore
    block_properties: CollectionProperty(
        name="Properties",
        type=BlockProperty,
    ) # type: ignore


classes = (
    BlockProperty,
    McbdeMenuProperties,
    McbdeBlockData,
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    Object.mcbde = PointerProperty(type=McbdeBlockData)
    Scene.mcbde = PointerProperty(type=McbdeMenuProperties)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)

    del Object.mcbde
    del Scene.mcbde