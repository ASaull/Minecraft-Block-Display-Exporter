import bpy
from mathutils import Vector
from math import radians

from .data_loader import data_loader


"""
Sets the origin of obj to an exact world location
"""
def origin_to_location(obj, location):
    old_active = bpy.context.active_object
    old_cursor_location = Vector((0, 0, 0)) + bpy.context.scene.cursor.location
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
    
    obj.select_set(False)

    for obj in tmp_selected:
        obj.select_set(True)



"""
Set the origin of a single object to its Minecraft origin corner
"""
def object_origin_to_corner(obj):
    obj.select_set(True)
    # Vertex 2 corresponds to the origin of a Minecraft block in Minecraft
    bottom_left_location = obj.matrix_world @ obj.data.vertices[2].co
    bpy.context.scene.cursor.location = bottom_left_location
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.select_set(False)


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
    Change the block type for selected objects.
    """
    print("|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n")
    print(self["block_type"])
    for obj in context.selected_objects:
        obj.mcbde["block_type"] = self["block_type"]
    print("Changing material for " + context.active_object.name + " to " + self.block_type)


    ####################################################################################
    active_object = bpy.context.view_layer.objects.active

    active_object.display_type = 'BOUNDS'

    for child in active_object.children:
        bpy.data.objects.remove(child, do_unlink=True)
        
    # Create inner object
    block_type = active_object.mcbde.block_type


    ############################
    ### GET BLOCKSTATE   #######
    ##########################################################################################

    # Two options, either the user has just set it, or we have to use the default.
    # For now, just assume that we use the default
    #####################################################################################
    blockstate = data_loader.get_data("blockstates", block_type)
    print("BLOCKSTATE:", blockstate)

    if True:  # The user has not set the variant, get the first one
        if blockstate["variants"]:  # this is an object that uses variants
            variant_data = blockstate["variants"]
            # The first key will be the default variation for the block
            selected_variant = next(iter(variant_data))
            active_object.mcbde["block_variant"] = selected_variant
        else:
            print("not a valid object")
    else:
        # This is for if the user has set the variant.
        pass

    # Now we have a variant, find the model
    selected_variant_data = variant_data[active_object.mcbde.block_variant]
    print("VARIANT DATA: ", selected_variant_data)
    if isinstance(selected_variant_data, list): # This happens when there are random variations. We just pick the first
        selected_variant_data = selected_variant_data[0]
        
    model_rotation = Vector((
        radians(selected_variant_data.get('x', 0)),
        radians(selected_variant_data.get('z', 0)),
        radians(-selected_variant_data.get('y', 0))
    ))

    model_name = selected_variant_data["model"].split('/')[-1]
    model_data = data_loader.get_data("block_models", model_name)
    print("MODEL NAME:", model_name)
    print("MODEL DATA:", model_data)

    while "parent" in model_data.keys() and model_data["parent"] != "block/block": # We do not need gui data from block/block
        parent_name = model_data["parent"].split("/")[-1]
        parent_data = data_loader.get_data("block_models", parent_name)
        del model_data["parent"]

        for key in parent_data.keys():
            if key == "textures" and "textures" in model_data:  # Special case for textures where we update variables
                tmp_textures = parent_data["textures"]
                print("TEMP TEXTURES:", tmp_textures)
                for texture_name in tmp_textures:
                    print("TEXTURE NAME:", texture_name)
                    texture_value = tmp_textures[texture_name]
                    tmp_textures[texture_name] = model_data["textures"].get(texture_value.strip('#'))
                for texture_name in model_data["textures"]:
                    if texture_name not in tmp_textures:
                        tmp_textures[texture_name] = model_data["textures"][texture_name]
                model_data[key] = tmp_textures
            elif key != "display":  # Otherwise, we just put the parent non-display data into the model data
                model_data[key] = parent_data[key]
        
    print("MODEL DATA:", model_data)

    # Now we have complete elements data, and texture data.
    # So we sub the textures into the elements data.

    if "elements" not in model_data.keys(): # In this case, there is no model
        # TODO RETURN
        pass

    replace_textures(model_data["elements"], model_data["textures"])

    elements = model_data["elements"]

    convert_elements_coordinates(elements)

    print("ELEMENTS:", elements)


    ######################################################################################


    ##########################################
    ### CREATE THE MODEL FROM ELEMENTS #######
    ##########################################################################################

    for element in elements:
        bpy.ops.mesh.primitive_cube_add(size=1)
        inner_object = bpy.context.active_object
        object_origin_to_corner(inner_object)
        
        # Creating the unscaled mesh at the centre of the world
        inner_object.scale.x = abs((element["to"].x - element["from"].x))
        inner_object.scale.y = abs((element["to"].y - element["from"].y))
        inner_object.scale.z = abs((element["to"].z - element["from"].z))
        inner_object.location = element["from"]
        
        # Now we have to rotate to match the variant rotation
        print("MODEL ROTATION: ", model_rotation)
        origin_to_location(inner_object, Vector((0.5, -0.5, 0.5)))
        inner_object.rotation_euler = model_rotation
        
        # Applying scale
        bpy.context.view_layer.objects.active = inner_object
        inner_object.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        inner_object.select_set(False)

        # Parent the inner object to the outer cube
        inner_object.parent = active_object
        inner_object.matrix_parent_inverse = active_object.matrix_world.inverted()
        
        # Translating that mesh to the location, rotation, and scale of its parent
        inner_object.location = inner_object.parent.location
        inner_object.scale = inner_object.parent.scale
        inner_object.rotation_euler = inner_object.parent.rotation_euler

        # Set inner object as non-interactable, and remove its block type
        inner_object.hide_select = True
        inner_object.mcbde["block_type"] = ""

        # Set the parent back to being the active object
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = active_object
        active_object.select_set(True)

    #########################################################################################