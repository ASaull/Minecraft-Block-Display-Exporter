import bpy
from mathutils import Vector, Matrix
from math import radians
import logging
import bmesh
import copy

from .data_loader import data_loader
from .utils import deselect_all_except, reselect

logger = logging.getLogger(__name__)


def origin_to_location(obj, location):
    """
    Sets the origin of obj to an exact world location
    """
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


def object_origin_to_corner(obj):
    """
    Set the origin of a single object to its Minecraft origin corner
    """
    old_cursor_location = Vector(bpy.context.scene.cursor.location)
    
    obj.select_set(True)
    # Vertex 2 corresponds to the origin of a Minecraft block in Minecraft
    bottom_left_location = obj.matrix_world @ obj.data.vertices[2].co
    bpy.context.scene.cursor.location = bottom_left_location
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.select_set(False)

    bpy.context.scene.cursor.location = old_cursor_location


def replace_textures(d, textures):
    """
    Replaces all instances of a # variable in d (#east for example) with the corresponding texture in textures
    """
    if isinstance(d, dict):
        for key, value in d.items():
            d[key] = replace_textures(value, textures)
    elif isinstance(d, list):
        for i, item in enumerate(d):
            d[i] = replace_textures(item, textures)
    elif isinstance(d, str) and d.startswith("#") and d[1:] in textures:
        print("replacing", d, "with", textures[d[1:]].replace("minecraft:", ""))
        return textures[d[1:]].replace("minecraft:", "")
    elif isinstance(d, str) and d.startswith("#") and d[1:] == "texture": # I have no idea why this case exists
        return textures["particle"].replace("minecraft:", "")
    return d

def convert_vector_coordinates(minecraft_vector):
    """
    Converts a list in the Minecraft format [x, y, z] to a Blender Vector
    """
    blender_vector = Vector((0, 0, 0))
    # Blender X from Minecraft X
    blender_vector[0] = minecraft_vector[0]/16
    # Blender Y from Minecraft -Z
    blender_vector[1] = -minecraft_vector[2]/16
    # Blender Z from Minecraft Y
    blender_vector[2] =  minecraft_vector[1]/16
    return blender_vector


def convert_elements_coordinates(elements):
    """
    Converts all coordinates in elements from Minecraft to Blender.
    Note that entries in the vector are floats so will not be perfectly precise.
    """
    for element in elements:
        for coordinate in ["from", "to"]:
            element[coordinate] = convert_vector_coordinates(element[coordinate])


def convert_element_rotation(rotation_dict):
    """
    Converts the Minecraft element rotations to rotation matrices that can
    be directly applied by Blender
    """
    if rotation_dict["axis"] == 'x':
        axis = 'X'
        angle = radians(rotation_dict["angle"])
    elif rotation_dict["axis"] == 'z':
        axis = 'Y'
        angle = -radians(rotation_dict["angle"])
    elif rotation_dict["axis"] == 'y':
        axis = 'Z'
        angle = radians(rotation_dict["angle"])

    element_rotation_matrix = Matrix.Rotation(angle, 4, axis)
    cent = convert_vector_coordinates(rotation_dict["origin"])

    return element_rotation_matrix, cent


def create_materials(obj, textures):
    print("creating materials for ", obj.name, " with ", textures)
    materials = []
    for texture in textures:
        material_name = textures[texture]

        if material_name in [m.name for m in materials]:
            # This is a duplicate texture, continue to the next
            continue

        if material_name not in [m.name for m in bpy.data.materials]:
            # Material does not exist yet
            image = data_loader.load_image(material_name)

            material = bpy.data.materials.new(name=material_name)
            material.use_nodes = True

            bsdf_node = material.node_tree.nodes["Principled BSDF"]

            tex_node = material.node_tree.nodes.new('ShaderNodeTexImage')
            tex_node.image = image
            tex_node.interpolation = "Closest"

            material.node_tree.links.new(tex_node.outputs[0], bsdf_node.inputs[0])
        else:
            # Material already exists
            print("material already exists")
            material = bpy.data.materials[material_name]

        materials.append(material)

    return materials


def update_face_material(face, material_index, bm, uv):
    """
    This will apply the specified material to the specified face

    Note that Blender uvs start from the bottom left, while
    Minecraft uvs start from the top left
    
    uv is [x1, y1, x2, y2]
    """
    uv_layer = bm.loops.layers.uv.active

    face.material_index = material_index

    loop_data = face.loops

    print("UV:", uv)

    # bottom left
    uv_data = loop_data[0][uv_layer].uv
    uv_data.x = uv[0]/16 #x1
    uv_data.y = 1 - uv[3]/16 #1 - y2

    # bottom right
    uv_data = loop_data[1][uv_layer].uv
    uv_data.x = uv[2]/16 #x2
    uv_data.y = 1 - uv[3]/16 #1 - y2

    # top right
    uv_data = loop_data[2][uv_layer].uv
    uv_data.x = uv[2]/16 #x2
    uv_data.y = 1 - uv[1]/16 #1 - y1

    # top left
    uv_data = loop_data[3][uv_layer].uv
    uv_data.x = uv[0]/16 #x1
    uv_data.y = 1 - uv[1]/16 #1 - y1


def change_block_type(self, context):
    """
    Called when block type is changed. In this case, we reset the variant to the
    default, assuming that the user does not want to preserve the indicated variant.

    This will fail on incorrect block type
    """
    block_type = copy.deepcopy(self["block_type"])
    tmp_selected = context.selected_objects
    tmp_active = context.active_object

    # The origin command block will just display as a command block
    if block_type == "origin_command_block":
        block_type = "command_block"

    # First get the default variant for this block type
    blockstate = data_loader.get_data("blockstates", block_type)
    print("BLOCKSTATE:", blockstate)

    if blockstate.get("variants", False):  # this is an object that uses variants
        variant_data = blockstate["variants"]
        # The first key will be the default variation for the block
        selected_variant = next(iter(variant_data))
    else:
        print("not a valid object - for now")
        return

    # Then we update the block properties and visuals of all selected blocks,
    # starting with the active object
    for obj in [tmp_active] + [o for o in tmp_selected if o != tmp_active]:
        print("updating for " + obj.name)
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
    block_type = copy.deepcopy(self["block_type"])
    tmp_selected = context.selected_objects
    tmp_active = context.active_object

    # The origin command block will just display as a command block
    if block_type == "origin_command_block":
        block_type = "command_block"

    blockstate = data_loader.get_data("blockstates", block_type)
    print("BLOCKSTATE:", blockstate)

    # TODO We must account for non-variant style blocks (fences)
    variant_data = blockstate["variants"]
    selected_variant = self["block_variant"]

    # Then we update the block properties and visuals of all selected blocks
    for obj in tmp_selected:
        obj.mcbde["block_variant"] = selected_variant

        change_block_visuals(obj, variant_data)

    # Finally, we reset the active and selected objects
    context.view_layer.objects.active = tmp_active
    for obj in tmp_selected:
        obj.select_set(True)


def change_block_visuals(obj, variant_data):
    # Get the correct variant
    selected_variant_data = variant_data[obj.mcbde.block_variant]
    print("VARIANT DATA: ", selected_variant_data)
    # If there are random variations we just pick the first
    if isinstance(selected_variant_data, list):
        selected_variant_data = selected_variant_data[0]

    model_name = selected_variant_data["model"].split('/')[-1]
    model_data = data_loader.get_data("block_models", model_name)
    print("MODEL NAME:", model_name)
    print("MODEL DATA 1:", model_data)

    # At this point, we check if this model has already been created in the scene and reference it
    for o in bpy.data.objects:
        if o != obj and o.data.name == obj.mcbde.block_type + "-" + obj.mcbde.block_variant:
            print("Mesh already exist on object " + o.name)
            obj.data = o.data
            return
        
    # Removing previous block visuals
    bpy.ops.object.mode_set(mode='EDIT')
    mesh = bpy.context.edit_object.data
    bm = bmesh.from_edit_mesh(mesh)
    bmesh.ops.delete(bm, geom=bm.verts, context='VERTS')
    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Removing materials
    obj.data.materials.clear()

    # We get the model rotation from the variant data
    rotation_matrix_x = Matrix.Rotation(radians( selected_variant_data.get('x', 0)), 4, 'X')
    rotation_matrix_y = Matrix.Rotation(radians( selected_variant_data.get('z', 0)), 4, 'Y')
    rotation_matrix_z = Matrix.Rotation(radians(-selected_variant_data.get('y', 0)), 4, 'Z')

    model_rotation = rotation_matrix_x @ rotation_matrix_y @ rotation_matrix_z

    # While this model data has a valid parent, we combine it with its parent to get all data
    # We do not need gui data from block/block
    while "parent" in model_data.keys() and model_data["parent"] != "block/block":
        parent_name = model_data["parent"].split("/")[-1]
        parent_data = data_loader.get_data("block_models", parent_name)
        del model_data["parent"]

        for key in parent_data.keys():
            # Special case for textures where we gather texture data into one dict
            if key == "textures" and "textures" in model_data:
                tmp_textures = parent_data["textures"]
                print("TEMP TEXTURES:", tmp_textures)

                for texture_name in tmp_textures:
                    print("TEXTURE NAME:", texture_name)
                    texture_value = tmp_textures[texture_name]

                    # If this texture is a reference to another texture, we go find that other texture
                    if '#' in texture_value:
                        tmp_textures[texture_name] = model_data["textures"].get(texture_value.strip('#'))
                    else:
                        tmp_textures[texture_name] = texture_value

                for texture_name in model_data["textures"]:
                    if texture_name not in tmp_textures:
                        tmp_textures[texture_name] = model_data["textures"][texture_name]

                model_data[key] = tmp_textures

            # Otherwise, we just put the parent non-display data into the model data
            elif key != "display":
                model_data[key] = parent_data[key]
        
    print("MODEL DATA 2:", model_data)

    # Now we have complete elements data, and texture data

    # If there is no model (air) we return
    if "elements" not in model_data.keys():
        return

    # Replacing '#' variables in data with the correct values
    replace_textures(model_data["elements"], model_data["textures"])

    # Some textures have "minecraft:" in them, others do not, we make this
    # consistent
    for texture_name in model_data["textures"]:
        model_data["textures"][texture_name] = model_data["textures"][texture_name].replace("minecraft:", "")

    print("MODEL DATA 3:", model_data)

    # We can now update the materials we need for out object
    materials = create_materials(obj, model_data["textures"])
    for material in materials:
        if material.name not in [m.name for m in obj.data.materials]:
            obj.data.materials.append(material)

    elements = model_data["elements"]

    # Converting Minecraft coordinates into Blender coordinates
    convert_elements_coordinates(elements)

    print("ELEMENTS:", elements)

    # We now create the model from the list of elements
    # We need to be in edit mode to add meshes
    bpy.ops.object.mode_set(mode='EDIT')

    for element in elements:
        mesh = bpy.context.edit_object.data
        bm = bmesh.from_edit_mesh(mesh)

        from_vector = element["from"]
        to_vector = element["to"]

        # This constructs a rectangular prism from "from_vector" to "to_vector"
        verts = [
            bm.verts.new(from_vector),
            bm.verts.new(Vector((from_vector.x, from_vector.y, to_vector.z))),
            bm.verts.new(Vector((to_vector.x, from_vector.y, from_vector.z))),
            bm.verts.new(Vector((to_vector.x, from_vector.y, to_vector.z))),
            bm.verts.new(Vector((from_vector.x, to_vector.y, from_vector.z))),
            bm.verts.new(Vector((from_vector.x, to_vector.y, to_vector.z))),
            bm.verts.new(Vector((to_vector.x, to_vector.y, from_vector.z))),
            bm.verts.new(to_vector),
        ]

        default_uv = [0, 0, 16, 16]

        # Fill in correct faces if they are present
        if "down" in element["faces"]:
            face = bm.faces.new((verts[0], verts[2], verts[6], verts[4]))
            
            face_data = element["faces"]["down"]
            material_index = materials.index(obj.data.materials[face_data["texture"]])
            update_face_material(face, material_index, bm, face_data.get("uv", default_uv))
        if "up" in element["faces"]:
            face = bm.faces.new((verts[5], verts[7], verts[3], verts[1]))

            print("UP TEXTURE", face_data["texture"])
            
            face_data = element["faces"]["up"]
            material_index = materials.index(obj.data.materials[face_data["texture"]])
            update_face_material(face, material_index, bm, face_data.get("uv", default_uv))
        if "west" in element["faces"]:
            face = bm.faces.new((verts[0], verts[4], verts[5], verts[1]))
            
            face_data = element["faces"]["west"]
            material_index = materials.index(obj.data.materials[face_data["texture"]])
            update_face_material(face, material_index, bm, face_data.get("uv", default_uv))
        if "east" in element["faces"]:
            face = bm.faces.new((verts[6], verts[2], verts[3], verts[7]))
            
            face_data = element["faces"]["east"]
            material_index = materials.index(obj.data.materials[face_data["texture"]])
            update_face_material(face, material_index, bm, face_data.get("uv", default_uv))
        if "south" in element["faces"]:
            face = bm.faces.new((verts[4], verts[6], verts[7], verts[5]))
            
            face_data = element["faces"]["south"]
            material_index = materials.index(obj.data.materials[face_data["texture"]])
            update_face_material(face, material_index, bm, face_data.get("uv", default_uv))
        if "north" in element["faces"]:
            face = bm.faces.new((verts[2], verts[0], verts[1], verts[3]))

            face_data = element["faces"]["north"]
            material_index = materials.index(obj.data.materials[face_data["texture"]])
            update_face_material(face, material_index, bm, face_data.get("uv", default_uv))

        # Element rotation, rotation may be defined for a single element
        if "rotation" in element:
            rotation_matrix, cent = convert_element_rotation(element["rotation"])
            bmesh.ops.rotate(bm, verts=verts, cent=cent, matrix=rotation_matrix)

        # Variant rotation, rotation defined for the whole block, and applied to all elements
        bmesh.ops.rotate(bm, verts=verts, cent=(0.5, -0.5, 0.5), matrix=model_rotation)

    # Give this mesh a name, unique to the mesh so we can reuse it
    obj.data.name = obj.mcbde.block_type + "-" + obj.mcbde.block_variant

    bpy.ops.object.mode_set(mode='OBJECT')