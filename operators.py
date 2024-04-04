import bpy
from bpy.types import Operator
from mathutils import Vector, Matrix

from .data_loader import data_loader


def convert_coordinates(blender_matrix):
    """
    Convert Blender coordinates to Minecraft coordinates
    """
    minecraft_matrix = Matrix((
        ( blender_matrix[0][0],  blender_matrix[0][2], -blender_matrix[0][1],  blender_matrix[0][3]),
        ( blender_matrix[2][0],  blender_matrix[2][2], -blender_matrix[2][1],  blender_matrix[2][3] - 1),
        (-blender_matrix[1][0], -blender_matrix[1][2],  blender_matrix[1][1], -blender_matrix[1][3]),
        (0, 0, 0, 1)
    ))
    return minecraft_matrix


def get_property_string(obj):
    formatted_property_pairs = [f'{property.name}:"{property.value}"' for property in obj.mcbde.block_properties]
    property_string = ','.join(formatted_property_pairs)
    return property_string


def determine_origin_location():
    """
    Return the starting point of the display entity in Minecraft.
    
    Default origin location is offset to the top north west corner of a command block at 0, 0, 0
    """
    ORIGIN_OFFSET = Vector((-0.5, 0.5, 0.5))
    
    origin_location = origin_location + ORIGIN_OFFSET

    # account for Blender to Minecraft difference
    origin_location = Vector((origin_location[0], origin_location[2], -origin_location[1]))

    return origin_location
        

class GenerateButton(Operator):
    """
    Operator for the generate button.
    """
    bl_idname = "object.generate_button"
    bl_label = "Generate"
    bl_description = "Generate command"

    def execute(self, context):
        origin_location = determine_origin_location()
        origin_text = f"~{round(origin_location[0], 4)} ~{round(origin_location[1], 4)} ~{round(origin_location[2], 4)}"
                
        command_string = "/summon block_display " + origin_text + " {Passengers: ["

        # Getting the string for each block (Passenger) in the command
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.mcbde and obj.mcbde.block_type not in [""]:
                blender_matrix = obj.matrix_world.copy()
                minecraft_matrix = convert_coordinates(blender_matrix)
                transformation_string = (
                    f"transformation: [{round(minecraft_matrix[0][0], 4)}f, {round(minecraft_matrix[0][1], 4)}f, {round(minecraft_matrix[0][2], 4)}f, {round(minecraft_matrix[0][3], 4)}f, "
                                     f"{round(minecraft_matrix[1][0], 4)}f, {round(minecraft_matrix[1][1], 4)}f, {round(minecraft_matrix[1][2], 4)}f, {round(minecraft_matrix[1][3], 4)}f, "
                                     f"{round(minecraft_matrix[2][0], 4)}f, {round(minecraft_matrix[2][1], 4)}f, {round(minecraft_matrix[2][2], 4)}f, {round(minecraft_matrix[2][3], 4)}f, "
                                     f"{round(minecraft_matrix[3][0], 4)}f, {round(minecraft_matrix[3][1], 4)}f, {round(minecraft_matrix[3][2], 4)}f, {round(minecraft_matrix[3][3], 4)}f]"
                )
                block_type = obj.mcbde.block_type

                # Getting the properties string
                property_string = get_property_string(obj)

                block_string = f'{{id: "minecraft:block_display", block_state: {{Name: "minecraft:{block_type}", Properties: {{{property_string}}}}},' \
                            + transformation_string + '},'
                command_string = command_string + block_string

        # Trim the last comma and close the brackets
        command_string = command_string[:-1] + ']}'
        context.scene.mcbde.command = command_string

        return {'FINISHED'}

    
class LoadDataButton(Operator):
    """
    Opeartor for the loading data button
    """
    bl_idname = "object.load_data_button"
    bl_label = "Load Data"
    bl_description = "Load the Minecraft data from the specified Minecraft install location"

    def execute(self, context):
        minecraft_location = context.scene.mcbde["minecraft_location"]
        data_loader.initialize_data(minecraft_location)
        return {'FINISHED'}


classes = (
    GenerateButton,
    LoadDataButton,
)

def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)