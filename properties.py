from bpy.types import PropertyGroup, PropertyGroup, Scene, Object
from bpy.props import (
    EnumProperty,
    StringProperty,
    PointerProperty,
)
from . import block_definitions
import mathutils


def convert_coordinates(blender_matrix):
    """
    Convert Blender coordinates to Minecraft coordinates.
    """
    minecraft_matrix = mathutils.Matrix((
        blender_matrix[0],
        blender_matrix[2],
        -blender_matrix[1],
        (0, 0, 0, 1)
    ))
    print(minecraft_matrix)
    return minecraft_matrix


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
    block_type: EnumProperty(
        items=(
            ("origin_command_block", "Origin Command Block", "The Command Block from which the command is run. You may only have one of these"),
            ("stone", "Stone", "Stone"),
            ("dirt", "Dirt", "Dirt"),
        ),
        name="Block Type",
        default="stone",
        description="The type of Minecraft block associated with this mesh",
        update=change_block_type
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
    print("set object and scene mcbde")


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)

    del Object.mcbde
    del Scene.mcbde