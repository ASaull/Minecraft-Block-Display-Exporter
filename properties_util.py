import bpy
from mathutils import Vector, Matrix
from math import radians
import logging
import bmesh

from .data_loader import data_loader
from .utils import deselect_all_except, reselect

logger = logging.getLogger(__name__)

"""
Sets the origin of obj to an exact world location
"""
def origin_to_location(obj, location):
    old_active = bpy.context.active_object
    old_cursor_location = Vector(bpy.context.scene.cursor.location)
    old_cursor_mode = bpy.context.scene.tool_settings.transform_pivot_point
    tmp_selected = bpy.context.selected_objects
    
    obj.select_set(True)
    
    # Set the 3D cursor to the desired location
    bpy.context.scene.cursor.location = location
    bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'

    # Set the object's origin to the 3D cursor location
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    
    # Revert cursor location
    bpy.context.view_layer.objects.active = old_active
    bpy.context.scene.cursor.location = old_cursor_location
    bpy.context.scene.tool_settings.transform_pivot_point = old_cursor_mode
    
    obj.select_set(False)

    for obj in tmp_selected:
        obj.select_set(True)



"""
Set the origin of a single object to its Minecraft origin corner
"""
def object_origin_to_corner(obj):
    old_cursor_location = Vector(bpy.context.scene.cursor.location)
    
    obj.select_set(True)
    # Vertex 2 corresponds to the origin of a Minecraft block in Minecraft
    bottom_left_location = obj.matrix_world @ obj.data.vertices[2].co
    bpy.context.scene.cursor.location = bottom_left_location
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.select_set(False)

    bpy.context.scene.cursor.location = old_cursor_location


"""
Replaces all instances of a # variable in d (#east for example) with the corresponding texture in textures
"""
def replace_textures(d, textures):
    if isinstance(d, dict):
        for key, value in d.items():
            d[key] = replace_textures(value, textures)
    elif isinstance(d, list):
        for i, item in enumerate(d):
            d[i] = replace_textures(item, textures)
    elif isinstance(d, str) and d.startswith("#") and d[1:] in textures:
        return textures[d[1:]].split('/')[-1]
    elif isinstance(d, str) and d.startswith("#") and d[1:] == "texture": # I have no idea why this case exists
        return textures["particle"].split('/')[-1]
    return d


"""
Converts all coordinates in elements from Minecraft to Blender
"""
def convert_elements_coordinates(elements):
    for element in elements:
        for coordinate in ["from", "to"]:
            blender_coordinate = Vector((0, 0, 0))
            # Blender X from Minecraft X
            blender_coordinate[0] = element[coordinate][0]/16
            # Blender Y from Minecraft -Z
            blender_coordinate[1] = -element[coordinate][2]/16
            # Blender Z from Minecraft Y
            blender_coordinate[2] = element[coordinate][1]/16
            element[coordinate] = blender_coordinate


def change_block_type(self, context):
    """
    Called when block type is changed. In this case, we reset the variant to the
    default, assuming that the user does not want to preserver the indicated variant.

    This will fail on incorrect block type
    """
    block_type = self["block_type"]
    tmp_selected = context.selected_objects
    tmp_active = context.active_object

    # First get the default variant for this block type
    blockstate = data_loader.get_data("blockstates", block_type)
    print("BLOCKSTATE:", blockstate)

    if blockstate["variants"]:  # this is an object that uses variants
        variant_data = blockstate["variants"]
        # The first key will be the default variation for the block
        selected_variant = next(iter(variant_data))
    else:
        print("not a valid object - for now")

    # Then we update the block properties and visuals of all selected blocks
    for obj in context.selected_objects:
        obj.mcbde["block_type"] = block_type
        obj.mcbde["block_variant"] = selected_variant

        change_block_visuals(obj, variant_data)

    # Finally, we reset the active and selected objects
    context.view_layer.objects.active = tmp_active
    for obj in tmp_selected:
        obj.select_set(True)


def change_block_variant(self, context):
    """
    Called when block variant is changed. In this case, we update block variant for
    all selected blocks to the user selected block variant, and do not reset to
    default.
    
    Note that we do not set the block type to be the same as the active block.
    This will, for example, allow the user to set the axis for several different logs.

    This will fail on incorrect block variant.
    """
    block_type = self["block_type"]
    tmp_selected = context.selected_objects
    tmp_active = context.active_object

    blockstate = data_loader.get_data("blockstates", block_type)
    print("BLOCKSTATE:", blockstate)

    # TODO We must account for non-variant style blocks (fences)
    variant_data = blockstate["variants"]
    selected_variant = self["block_variant"]

    # Then we update the block properties and visuals of all selected blocks
    for obj in context.selected_objects:
        obj.mcbde["block_variant"] = selected_variant

        change_block_visuals(obj, variant_data)

    # Finally, we reset the active and selected objects
    context.view_layer.objects.active = tmp_active
    for obj in tmp_selected:
        obj.select_set(True)


def change_block_visuals(obj, variant_data):
    #object_origin_to_corner(obj)

    # Block scale must equal dimensions to be used with this addon
    # if not obj.scale == obj.dimensions:
    #     current_dimensions = Vector(obj.dimensions)
    #     obj.dimensions = Vector((1, 1, 1))
    #     prev = deselect_all_except(obj)
    #     bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    #     reselect(prev)
    #     print("current_d", current_dimensions)
    #     obj.scale = current_dimensions
    #     print("scale", obj.scale)

    # Setting the object to wireframe so we can see the visual
    # obj.display_type = ''

    # Removing previous block visuals
    bpy.ops.object.mode_set(mode='EDIT')
    mesh = bpy.context.edit_object.data
    bm = bmesh.from_edit_mesh(mesh)
    bmesh.ops.delete(bm, geom=bm.verts, context='VERTS')
    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Now we have a variant, find the model
    selected_variant_data = variant_data[obj.mcbde.block_variant]
    print("VARIANT DATA: ", selected_variant_data)
    if isinstance(selected_variant_data, list): # This happens when there are random variations. We just pick the first
        selected_variant_data = selected_variant_data[0]
        
    # model_rotation = Vector((
    #     radians( selected_variant_data.get('x', 0)),
    #     radians( selected_variant_data.get('z', 0)),
    #     radians(-selected_variant_data.get('y', 0))
    # ))
    # We get the model rotation from the variant data
    rotation_matrix_x = Matrix.Rotation(radians( selected_variant_data.get('x', 0)), 4, 'X')
    rotation_matrix_y = Matrix.Rotation(radians( selected_variant_data.get('z', 0)), 4, 'Y')
    rotation_matrix_z = Matrix.Rotation(radians(-selected_variant_data.get('y', 0)), 4, 'Z')

    model_rotation = rotation_matrix_x @ rotation_matrix_y @ rotation_matrix_z


    model_name = selected_variant_data["model"].split('/')[-1]
    model_data = data_loader.get_data("block_models", model_name)
    print("MODEL NAME:", model_name)
    print("MODEL DATA 1:", model_data)

    # While this model data has a valid parent, we combine it with its parent
    while "parent" in model_data.keys() and model_data["parent"] != "block/block":
        # We do not need gui data from block/block
        parent_name = model_data["parent"].split("/")[-1]
        parent_data = data_loader.get_data("block_models", parent_name)
        del model_data["parent"]

        for key in parent_data.keys():
            if key == "textures" and "textures" in model_data:
                # Special case for textures where we gather texture data into one dict
                tmp_textures = parent_data["textures"]
                print("TEMP TEXTURES:", tmp_textures)

                for texture_name in tmp_textures:
                    print("TEXTURE NAME:", texture_name)
                    texture_value = tmp_textures[texture_name]

                    # If this texture is a reference to another texture, we go find that other texture.
                    if '#' in texture_value:
                        tmp_textures[texture_name] = model_data["textures"].get(texture_value.strip('#'))
                    else:
                        tmp_textures[texture_name] = texture_value

                for texture_name in model_data["textures"]:
                    if texture_name not in tmp_textures:
                        tmp_textures[texture_name] = model_data["textures"][texture_name]

                model_data[key] = tmp_textures

            elif key != "display":
                # Otherwise, we just put the parent non-display data into the model data
                model_data[key] = parent_data[key]
        
    print("MODEL DATA 2:", model_data)

    # Now we have complete elements data, and texture data.
    # So we sub the textures into the elements data.

    if "elements" not in model_data.keys(): # In this case, there is no model (air)
        return

    replace_textures(model_data["elements"], model_data["textures"])

    elements = model_data["elements"]

    convert_elements_coordinates(elements)

    print("ELEMENTS:", elements)

    ######################################
    ### CREATE THE MODEL FROM ELEMENTS ###
    ######################################

    # We need to be in edit mode to add meshes
    bpy.ops.object.mode_set(mode='EDIT')

    for element in elements:

        mesh = bpy.context.edit_object.data
        bm = bmesh.from_edit_mesh(mesh)

        from_vector = element["from"]
        to_vector = element["to"]

        verts = [
            bm.verts.new(from_vector),
            bm.verts.new(Vector((to_vector.x, from_vector.y, from_vector.z))),
            bm.verts.new(Vector((to_vector.x, to_vector.y, from_vector.z))),
            bm.verts.new(Vector((from_vector.x, to_vector.y, from_vector.z))),
            bm.verts.new(to_vector),
            bm.verts.new(Vector((from_vector.x, to_vector.y, to_vector.z))),
            bm.verts.new(Vector((from_vector.x, from_vector.y, to_vector.z))),
            bm.verts.new(Vector((to_vector.x, from_vector.y, to_vector.z))),
        ]

        faces = [
            bm.faces.new((verts[0], verts[1], verts[2], verts[3])),
            bm.faces.new((verts[4], verts[5], verts[6], verts[7])),
            bm.faces.new((verts[0], verts[3], verts[5], verts[6])),
            bm.faces.new((verts[1], verts[2], verts[4], verts[7])),
            bm.faces.new((verts[2], verts[3], verts[5], verts[4])),
            bm.faces.new((verts[0], verts[1], verts[7], verts[6])),
        ]

        # Rotate the cube
        bmesh.ops.rotate(bm, verts=verts, cent=(0.5, -0.5, 0), matrix=model_rotation)

    bpy.ops.object.mode_set(mode='OBJECT')

        
    #########################################################################################