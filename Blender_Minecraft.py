bl_info = {
        "name": "Minecraft Block Display Exporter (MCBDE)",
        "author": "Aidan Saull",
        "version": (0, 0, 1),
        "blender": (4, 00, 0),
        "location": "View3D > UI > MCBDE",
        "description": "Allows exporting Blender cubes as Minecraft block displays.",
        "warning": "",
        "doc_url": "",
        "category": "3D View",
    }


import bpy
from bpy.types import Panel, PropertyGroup, Scene, WindowManager, Object, Operator
from bpy.props import (
    IntProperty,
    EnumProperty,
    StringProperty,
    PointerProperty,
)
import os
import mathutils
import json


minecraft_location = os.path.join(os.getenv('APPDATA'), ".minecraft","versions", "1.20.1","1.20.1.jar")


def convert_coordinates(blender_matrix):
    minecraft_matrix = mathutils.Matrix((
        blender_matrix[0],
        blender_matrix[2],
        -blender_matrix[1],
        (0, 0, 0, 1)
    ))

    print(minecraft_matrix)
    return minecraft_matrix


def origin_to_centre(self, context):
    old_active = context.active_object
    for object in context.selected_objects:
        context.view_layer.objects.active = object
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")
    context.view_layer.objects.active = old_active


def origin_to_corner(self, context):
    old_active = context.active_object
    # storing old cursor location must be done by value
    old_cursor_location = mathutils.Vector((0, 0, 0)) + context.scene.cursor.location
    # we make this temporary list so that we can iterate over previously selected objects
    tmp_selected = context.selected_objects
    bpy.ops.object.select_all(action='DESELECT')
    for object in tmp_selected:
        # set the active object to the current one in this for loop
        object.select_set(True)
        print(context.selected_objects)
        # get the location of the vertex we want
        bottom_left_location = object.matrix_world @ object.data.vertices[0].co
        # move the 3d cursor to that location
        context.scene.cursor.location = bottom_left_location
        # set the origin to the current location of the 3d cursor
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        # now deselect it
        object.select_set(False)
    # reset active object and cursor location
    context.view_layer.objects.active = old_active
    context.scene.cursor.location = old_cursor_location
    # reselect all now that we are done
    for object in tmp_selected:
        object.select_set(True)

def change_block_type(self, context):
    print(self["block_type"])
    # First we update the prop for all selected objects
    for object in context.selected_objects:
        object.mcbde["block_type"] = self["block_type"]
    # Then we set the material for all selected objects
    print("Changing material for " + context.active_object.name + " to " + self.block_type)


def get_texture(name):
    pass


def generate_command(self, context):
    origin_location = None
    # This is the start of the command
    command_string = "/summon block_display ~-0.5 ~-0.5 ~0.5 {Passengers: ["
    
    origin_to_corner(self, context)
    
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.mcbde:
            if obj.mcbde.block_type == "origin_command_block":
                # This is the origin block, so we can set the origin location now
                origin_location = obj.location
                break
    if origin_location == None: # In this case, no origin block, use default
        origin_location = mathutils.Vector((0, 0, 0))
    print("Command Block Origin at", origin_location)
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.mcbde and not obj.mcbde.block_type == "origin_command_block":
            minecraft_matrix = convert_coordinates(obj.matrix_world)
            # This is the transformation part of the string for this block
            transformation_string = (
                f"transformation: [{round(minecraft_matrix[0][0], 4)}f, {round(minecraft_matrix[0][1], 4)}f, {round(minecraft_matrix[0][2], 4)}f, {round(minecraft_matrix[0][3], 4)}f, "
                f"{round(minecraft_matrix[1][0], 4)}f, {round(minecraft_matrix[1][1], 4)}f, {round(minecraft_matrix[1][2], 4)}f, {round(minecraft_matrix[1][3], 4)}f, "
                f"{round(minecraft_matrix[2][0], 4)}f, {round(minecraft_matrix[2][1], 4)}f, {round(minecraft_matrix[2][2], 4)}f, {round(minecraft_matrix[2][3], 4)}f, "
                f"{round(minecraft_matrix[3][0], 4)}f, {round(minecraft_matrix[3][1], 4)}f, {round(minecraft_matrix[3][2], 4)}f, {round(minecraft_matrix[3][3], 4)}f]"
            )
            # Adding transformation string to the start of the block string with the correct block
            block_string = f'{{id: "minecraft:block_display", block_state: {{Name: "minecraft:{obj.mcbde.block_type}", Properties: {{}}}},'\
                + transformation_string + '},'
            command_string = command_string + block_string
    # Now we strip off the final comma and complete the bcrackets
    command_string = command_string[:-1] + ']}'
    print(command_string)
     

class McbdePanel(Panel):
    bl_idname = "MCBDE_Panel"
    bl_label = "MCBDE"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MCBDE"
    bl_options = {'HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        layout = self.layout
        active_object = context.active_object
        
        # Create a section for the selection
        layout.label(text="Selection:")
        col = layout.column()
        
        if active_object and active_object.type == 'MESH' and active_object.mcbde:
            col.prop(active_object.mcbde, "block_type", text="Block")
        else:
            layout.label(text="Select a mesh object with MCBDE properties.")
        
        row = layout.row(align=True)
        row.operator("object.origin_to_centre_button")
        row.operator("object.origin_to_corner_button")
        
        # Create a section for generation
        layout.label(text = "Generation:")
        col = layout.column()
            
        col.operator("object.generate_button")
        col.prop(context.scene.mcbde, "command")


class McbdeMenuProperties(PropertyGroup):
    command: StringProperty(
    name="Command",
    description="Copy this into your Command Block in Minecraft",
    default="",
    maxlen=2048,
    options={'HIDDEN', 'SKIP_SAVE'}
    )
    

class McbdeBlockProperties(PropertyGroup):
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
    
    
class GenerateButton(Operator):
    bl_idname = "object.generate_button"
    bl_label = "Generate"
    bl_description = "Generate command"

    def execute(self, context):
        generate_command(self, context)
        return {'FINISHED'}
    
class OriginToCentreButton(Operator):
    bl_idname = "object.origin_to_centre_button"
    bl_label = "Origin to Centre"
    bl_description = "Move the origins of all selected objects to their centres. Blender default, useful for manipulating objects"
    
    def execute(self, context):
        origin_to_centre(self, context)
        return {'FINISHED'}
    
    
class OriginToCornerButton(Operator):
    bl_idname = "object.origin_to_corner_button"
    bl_label = "Origin to Corner"
    bl_description = "Move the origins of all selected objects to the bottom corner. Minecraft default, useful for visualizing object origins within Minecraft"
    
    def execute(self, context):
        origin_to_corner(self, context)
        return {'FINISHED'}


classes = (
    McbdeMenuProperties,
    McbdeBlockProperties,
    McbdePanel,
    GenerateButton,
    OriginToCentreButton,
    OriginToCornerButton
)


def register():
    #the usual registration...
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    Object.mcbde = PointerProperty(type=McbdeBlockProperties)
    Scene.mcbde = PointerProperty(type=McbdeMenuProperties)


def unregister():
    #the usual unregistration in reverse order ...

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del Object.mcdbe


if __name__ == "__main__":
    register()