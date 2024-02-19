import bpy
from bpy.types import Operator
import mathutils


def origin_to_corner(context):
    old_active = context.active_object
    old_cursor_location = mathutils.Vector((0, 0, 0)) + context.scene.cursor.location
    tmp_selected = context.selected_objects

    bpy.ops.object.select_all(action='DESELECT')
    for obj in tmp_selected:
        obj.select_set(True)
        bottom_left_location = obj.matrix_world @ obj.data.vertices[2].co
        context.scene.cursor.location = bottom_left_location
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        obj.select_set(False)

    context.view_layer.objects.active = old_active
    context.scene.cursor.location = old_cursor_location

    for obj in tmp_selected:
        obj.select_set(True)


def convert_coordinates(blender_matrix):
    """
    Convert Blender coordinates to Minecraft coordinates.
    """
    print("Blender:\n", blender_matrix)
    minecraft_matrix = mathutils.Matrix((
        (blender_matrix[0][0], blender_matrix[0][2], -blender_matrix[0][1], blender_matrix[0][3]),
        (blender_matrix[2][0], blender_matrix[2][2], -blender_matrix[2][1], blender_matrix[2][3]-1),
        (-blender_matrix[1][0], -blender_matrix[1][2], blender_matrix[1][1], -blender_matrix[1][3]),
        (0, 0, 0, 1)
    ))
    print("Minecraft:\n", minecraft_matrix)
    return minecraft_matrix


class GenerateButton(Operator):
    """
    Operator for the generate button.
    """
    bl_idname = "object.generate_button"
    bl_label = "Generate"
    bl_description = "Generate command"

    def execute(self, context):
        origin_location = None
        command_string = "/summon block_display ~-0.5 ~0.5 ~-0.5 {Passengers: ["

        origin_to_corner(context)

        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.mcbde:
                if obj.mcbde.block_type == "origin_command_block":
                    origin_location = obj.location
                    break

        if origin_location is None:
            origin_location = mathutils.Vector((0, 0, 0))

        print("Command Block Origin at", origin_location)
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.mcbde and not obj.mcbde.block_type == "origin_command_block":
                minecraft_matrix = convert_coordinates(obj.matrix_world)
                transformation_string = (
                    f"transformation: [{round(minecraft_matrix[0][0], 4)}f, {round(minecraft_matrix[0][1], 4)}f, {round(minecraft_matrix[0][2], 4)}f, {round(minecraft_matrix[0][3], 4)}f, "
                    f"{round(minecraft_matrix[1][0], 4)}f, {round(minecraft_matrix[1][1], 4)}f, {round(minecraft_matrix[1][2], 4)}f, {round(minecraft_matrix[1][3], 4)}f, "
                    f"{round(minecraft_matrix[2][0], 4)}f, {round(minecraft_matrix[2][1], 4)}f, {round(minecraft_matrix[2][2], 4)}f, {round(minecraft_matrix[2][3], 4)}f, "
                    f"{round(minecraft_matrix[3][0], 4)}f, {round(minecraft_matrix[3][1], 4)}f, {round(minecraft_matrix[3][2], 4)}f, {round(minecraft_matrix[3][3], 4)}f]"
                )
                block_string = f'{{id: "minecraft:block_display", block_state: {{Name: "minecraft:{obj.mcbde.block_type}", Properties: {{}}}},' \
                            + transformation_string + '},'
                command_string = command_string + block_string

        command_string = command_string[:-1] + ']}'
        print(command_string)
        return {'FINISHED'}


class OriginToCentreButton(Operator):
    """
    Operator for the moving origins to the centre button.
    """
    bl_idname = "object.origin_to_centre_button"
    bl_label = "Origin to Centre"
    bl_description = "Move the origins of all selected objects to their centres. Blender default, useful for manipulating objects"

    def execute(self, context):
        old_active = context.active_object
        for obj in context.selected_objects:
            context.view_layer.objects.active = obj
            bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")
        context.view_layer.objects.active = old_active
        return {'FINISHED'}


class OriginToCornerButton(Operator):
    """
    Operator for the moving origins to the bottom corner button.
    """
    bl_idname = "object.origin_to_corner_button"
    bl_label = "Origin to Corner"
    bl_description = "Move the origins of all selected objects to the bottom corner. Minecraft default, useful for visualizing object origins within Minecraft"

    def execute(self, context):
        origin_to_corner(context)
        return {'FINISHED'}
    

classes = (
    GenerateButton,
    OriginToCentreButton,
    OriginToCornerButton,
)

def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)