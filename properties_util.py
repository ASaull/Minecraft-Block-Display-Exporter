import bpy
from mathutils import Vector, Matrix
from math import radians
import logging
import bmesh
import copy
import json

from .data_loader import data_loader

logger = logging.getLogger(__name__)


def deselect_all_except(obj) -> list:
    """
    Deselect all objects except the object obj, or list of objects obj

    Usage:
    prev = deselect_all_except(obj)
    Do Stuff
    reselect(prev)

    Args:
        obj (Object or list): must be a Blender object or a list of Blender objects

    Returns:
        A list of previously selected objects for use with reselect()
    """
    prev = bpy.context.selected_objects
    bpy.ops.object.select_all(action='DESELECT')

    if isinstance(obj, list):
        for obj in list:
            obj.select_set(True)
    else:
        obj.select_set(True)

    return prev


def replace_textures(d, textures):
    """
    Replace all instances of a # variable in d (#east for example) with the corresponding texture in textures
    """
    if isinstance(d, dict):
        for key, value in d.items():
            d[key] = replace_textures(value, textures)
    elif isinstance(d, list):
        for i, item in enumerate(d):
            d[i] = replace_textures(item, textures)
    elif isinstance(d, str) and d.startswith("#") and d[1:] in textures:
        return textures[d[1:]].replace("minecraft:", "")
    elif isinstance(d, str) and d.startswith("#") and d[1:] == "texture": # I have no idea why this case exists
        return textures["particle"].replace("minecraft:", "")
    return d

def convert_vector_coordinates(minecraft_vector):
    """
    Convert a list in the Minecraft format [x, y, z] to a Blender Vector
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
    Convert all coordinates in elements from Minecraft to Blender.
    Note that entries in the vector are floats so will not be perfectly precise.
    """
    for element in elements:
        for coordinate in ["from", "to"]:
            element[coordinate] = convert_vector_coordinates(element[coordinate])


def convert_element_rotation(rotation_dict):
    """
    Convert the Minecraft element rotations to rotation matrices that can
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


def create_materials(textures):
    """
    Create one material for each of the supplied textures if they
    do not already exist.
    """
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
            material.blend_method = 'CLIP'
            material.use_backface_culling = True

            bsdf_node = material.node_tree.nodes["Principled BSDF"]
            output_node = material.node_tree.nodes["Material Output"]
            transparent_node = material.node_tree.nodes.new("ShaderNodeBsdfTransparent")
            mix_node = material.node_tree.nodes.new("ShaderNodeMixShader")

            tex_node = material.node_tree.nodes.new('ShaderNodeTexImage')
            tex_node.image = image
            tex_node.interpolation = "Closest"

            material.node_tree.links.new(tex_node.outputs[0], bsdf_node.inputs[0])
            material.node_tree.links.new(tex_node.outputs[1], mix_node.inputs[0])
            material.node_tree.links.new(transparent_node.outputs[0], mix_node.inputs[1])
            material.node_tree.links.new(bsdf_node.outputs[0], mix_node.inputs[2])
            material.node_tree.links.new(mix_node.outputs[0], output_node.inputs[0])
        else:
            # Material already exists
            material = bpy.data.materials[material_name]

        materials.append(material)

    return materials


def update_face_material(face, material_index, image_size, bm, uv):
    """
    Apply the specified material to the specified face.

    Note that Blender uvs start from the bottom left, while
    Minecraft uvs start from the top left.
    
    uv format is [x1, y1, x2, y2] and is in Minecraft
    """
    uv_layer = bm.loops.layers.uv.active

    if uv_layer is None:
        uv_layer = bm.loops.layers.uv.new("UVMap")

    face.material_index = material_index

    loop_data = face.loops

    height_ratio = image_size[1]/image_size[0]

    # bottom left
    uv_data = loop_data[0][uv_layer].uv
    uv_data.x = uv[0]/16
    uv_data.y = (1 - uv[3]/16) / height_ratio

    # bottom right
    uv_data = loop_data[1][uv_layer].uv
    uv_data.x = uv[2]/16
    uv_data.y = (1 - uv[3]/16) / height_ratio

    # top right
    uv_data = loop_data[2][uv_layer].uv
    uv_data.x = uv[2]/16
    uv_data.y = (1 - uv[1]/16) / height_ratio

    # top left
    uv_data = loop_data[3][uv_layer].uv
    uv_data.x = uv[0]/16
    uv_data.y = (1 - uv[1]/16) / height_ratio


def add_to_dict(d, key, value):
    """
    Place value in the list under key in the dict,
    without repeating key or value in dict.

    If the value is none or false, we insert at the beginning
    so that it will be the default
    """
    if key not in d:
        d[key] = [value]
    elif value not in d[key]:
        d[key].append(value)


def process_part(d, part):
    for key, value in part.items():
        values = value.split('|')
        for value in values:
            add_to_dict(d, key, value)
            

def build_properties_dict(blockstate):
    """
    Build a dict that stores the full set of possible block properties
    for a given blockstate.

    Example return value:
    {'facing': ['north', 'east', 'west', 'south']}
    """
    possible_properties = {}

    if "variants" in blockstate:
        for variant in blockstate["variants"]:
            if variant == "":
                # In this case, there must be exactly one variant, and it is blank
                return {}
            for key, value in [key_value.split("=") for key_value in variant.split(",")]:
                add_to_dict(possible_properties, key, value)
    
    elif "multipart" in blockstate:
        for part in blockstate["multipart"]:
            if "when" not in part:
                # In this case, there are no properties in this part (just a model)
                continue
            when = part["when"]
            if "AND" in when:
                for w in when["AND"]:
                    process_part(possible_properties, w)
            elif "OR" in when:
                for w in when["OR"]:
                    process_part(possible_properties, w)
            else:
                process_part(possible_properties, when)
        
        # Ensure that true and false always both exist even if blockstate does not specify both
        # Also ensure none exists, if blockstate does not specify true and false
        # Place false and none at the beginning
        for property in possible_properties:
            property_list = possible_properties[property]
            if "true" in property_list and "false" not in property_list:
                property_list.append("false")
            elif "false" in property_list and "true" not in property_list:
                property_list.append("true")
            elif "true" not in property_list and "false" not in property_list and "none" not in property_list:
                property_list.append("none")
                
    else:
        print("Not a valid block model!")

    return possible_properties


def get_default_properties(block_properties):
    """
    Return the default (first) properties in block_properties as a dict.
    
    Example return value:
    {'facing': 'north'}
    """
    selected = {}

    for property in block_properties:
        if "false" in block_properties[property]:
            selected[property] = "false"
            if property == "up" and "north" in block_properties and "tall" in block_properties["north"]:
                # This is a wall, default to true instead
                selected[property] = "true"
            continue
        if "none" in block_properties[property]:
            selected[property] = "none"
            continue
        selected[property] = block_properties[property][0]

    return selected

def get_selected_properties(obj):
    """
    Return the properties which have been selected in obj as a dict
    
    Example return value:
    {'facing': 'north'}
    """
    selected = {}

    for property in obj.mcbde.block_properties:
        selected[property.name] = property.value
    
    return selected


def property_matches(selected_block_properties, when):
    """
    Return true if the selected block properties match the condition
    in when.
    """
    for property_name, property_value in when.items():
        property_values_split = property_value.split('|')
        if property_name not in selected_block_properties:
            return False
        if selected_block_properties[property_name] not in property_values_split:
            return False
    return True


def get_part_model(part, selected_block_properties):
    """
    Return the model in when 
    """
    when = part.get("when", None)
    if when:
        if "AND" in when:
            for w in when["AND"]:
                if not property_matches(selected_block_properties, w):
                    return None
            return part["apply"]
        elif "OR" in when:
            for w in when["OR"]:
                if property_matches(selected_block_properties, w):
                    return(part["apply"])
        else:
            if property_matches(selected_block_properties, when):
                return part["apply"]
    else:
        return part["apply"]


def get_outer_model_data(blockstate, selected_block_properties):
    """
    Return a list of model jsons corresponding to the
    selected block properties as defined in blockstate.

    This is a list because multipart blocks may have several models.
    """
    if "variants" in blockstate:
        variant_string = ""
        for property, value in selected_block_properties.items():
            variant_string = variant_string + property + "=" + value + ","
        variant_string = variant_string[:-1]
        for variant in blockstate["variants"]:
            if variant == variant_string:
                return [blockstate["variants"][variant]]
        return []
    elif "multipart" in blockstate:
        part_list = []
        for part in blockstate["multipart"]:
            part_model = get_part_model(part, selected_block_properties)
            if part_model: part_list.append(part_model)
        return part_list
    

def generate_default_uvs(from_vector, to_vector):
    """
    uv format is [x1, y1, x2, y2]
    """
    f = Vector((from_vector.x, -from_vector.y, from_vector.z))*16
    t = Vector((to_vector.x, -to_vector.y, to_vector.z))*16

    face_uvs = {}

    face_uvs["down"] = [f.x, 16-t.y, t.x, 16-f.y]
    face_uvs["up"] = [f.x, f.y, t.x, t.y]
    face_uvs["west"] = [f.y, 16-t.z, t.y, 16-f.z]
    face_uvs["east"] = [16-t.y, 16-t.z, 16-f.y, 16-f.z]
    face_uvs["south"] = [f.x, 16-t.z, t.x, 16-f.z]
    face_uvs["north"] = [16-t.x, 16-t.z, 16-f.x, 16-f.z]
        
        
    return face_uvs


def build_model(obj, outer_model_data, model_data):
    """
    Add the transformed cubes from the elements of model_data
    to the mesh data in obj.

    TODO:
    Refactor this out into several sub functions

    outer_model_data contains the rotation.
    """
    # Identity matrix, no rotation by default
    model_rotation = Matrix.Rotation(0, 4, 'X')

    # We get the model rotation from the variant data
    # Note that the order the rotation is applied is relevant,
    # and that there are no rotations in the Minecraft z direction
    for key in reversed(list(outer_model_data)):
        if key == 'x':
            part_rotation_matrix = Matrix.Rotation(-radians(outer_model_data[key]), 4, 'X')
        elif key == 'y':
            part_rotation_matrix = Matrix.Rotation(-radians(outer_model_data[key]), 4, 'Z')
        else:
            continue
        model_rotation = model_rotation @ part_rotation_matrix

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

                for texture_name in tmp_textures:
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

    # If there is no model (air) we return
    if "elements" not in model_data.keys():
        return

    # Replacing '#' variables in data with the correct values
    replace_textures(model_data["elements"], model_data["textures"])

    # Some textures have "minecraft:" in them, others do not, we make this
    # consistent
    for texture_name in model_data["textures"]:
        model_data["textures"][texture_name] = model_data["textures"][texture_name].replace("minecraft:", "")

    # We can now update the materials we need for out object
    materials = create_materials(model_data["textures"])
    for material in materials:
        if material.name not in [m.name for m in obj.data.materials]:
            obj.data.materials.append(material)

    elements = model_data["elements"]

    # Converting Minecraft coordinates into Blender coordinates
    convert_elements_coordinates(elements)

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

        default_uvs = generate_default_uvs(from_vector, to_vector)

        # Fill in correct faces if they are present
        face_vertex_mapping = {
            "down":  (0, 2, 6, 4),
            "up":    (5, 7, 3, 1),
            "west":  (0, 4, 5, 1),
            "east":  (6, 2, 3, 7),
            "south": (4, 6, 7, 5),
            "north": (2, 0, 1, 3)
        }

        for face_name, face_vertices in face_vertex_mapping.items():
            if face_name in element["faces"]:
                face = bm.faces.new((verts[i] for i in face_vertices))
                
                face_data = element["faces"][face_name]
                material = obj.data.materials[face_data["texture"]]
                material_index = materials.index(material)
                image_size = material.node_tree.nodes.get("Image Texture", None).image.size
                update_face_material(face, material_index, image_size, bm, face_data.get("uv", default_uvs[face_name]))

        # Element rotation, rotation may be defined for a single element
        if "rotation" in element:
            rotation_matrix, cent = convert_element_rotation(element["rotation"])
            bmesh.ops.rotate(bm, verts=verts, cent=cent, matrix=rotation_matrix)
            # if element["rotation"]["rescale"]:
            #     scale_factor = Vector((1.4142, 1.4142, 1))
            #     bmesh.ops.scale(bm, vec=scale_factor, verts=verts)

        # Variant rotation, rotation defined for the whole block, and applied to all elements
        bmesh.ops.rotate(bm, verts=verts, cent=(0.5, -0.5, 0.5), matrix=model_rotation)

    bpy.ops.object.mode_set(mode='OBJECT')


def update_block_properties(obj, selected_block_properties, block_properties=None, update_property=None):
    """
    Update obj to have the properties indicated in selected_block_properties.

    If block_properties are specified, also reset and update the available properties.

    If update_property is specified, only update that specific property.
    """
    if block_properties:
        obj.mcbde.block_properties.clear()

    if update_property and (obj.mcbde.block_properties is None or update_property not in obj.mcbde.block_properties):
        return

    for property in selected_block_properties:
        if block_properties:
            tmp_block_prop = obj.mcbde.block_properties.add()
            tmp_block_prop.value_options = json.dumps(block_properties[property])
            tmp_block_prop.name = property
            tmp_block_prop["value"] = selected_block_properties[property]
        elif update_property and update_property == property:
            tmp_block_prop = obj.mcbde.block_properties.get(property)
            tmp_block_prop["value"] = selected_block_properties[property]


def change_block_type(self, context):
    """
    Called when block type is changed.

    Change the model and data of the selected blocks to have the same
    model and data as the selected block type in the active block.
    """
    block_type = self["block_type"]
    selected = context.selected_objects
    active = context.active_object

    blockstate = data_loader.get_data("blockstates", block_type)
    
    block_properties = build_properties_dict(blockstate)

    selected_block_properties = get_default_properties(block_properties)

    outer_model_data = get_outer_model_data(blockstate, selected_block_properties)

    # Then we update the block properties and visuals of all selected blocks,
    # starting with the active object
    for obj in [active] + [o for o in selected if o != active]:
        obj.mcbde["block_type"] = block_type

        update_block_properties(obj, selected_block_properties, block_properties)

        change_block_visuals(obj, outer_model_data)

    for obj in selected:
        obj.select_set(True)
    context.view_layer.objects.active = active


def change_block_variant(self, context):
    """
    Called when block variant is changed.

    Change the model and data of the selected blocks to have the same
    model and data as the selected block type in the active block.
    
    Note that we do not set the block type to be the same as the active block.
    This will, for example, allow the user to set the axis for several different logs.
    """
    selected = context.selected_objects
    active = context.active_object
    
    selected_block_properties = get_selected_properties(active)

    # update the block visuals of all selected blocks, starting with the active block
    for obj in [active] + [o for o in selected if o != active]:
        block_type = obj.mcbde.block_type

        blockstate = data_loader.get_data("blockstates", block_type)

        
        update_block_properties(obj, selected_block_properties, update_property=self.name)

        selected_block_properties = get_selected_properties(obj)

        outer_model_data = get_outer_model_data(blockstate, selected_block_properties)

        if outer_model_data is None:
            continue

        change_block_visuals(obj, outer_model_data)
    
    for obj in selected:
        obj.select_set(True)
    context.view_layer.objects.active = active


def change_block_visuals(obj, outer_model_data):
    """
    
    """
    deselect_all_except(obj)
    bpy.context.view_layer.objects.active = obj


    variant_name = ""
    for block_property in obj.mcbde.block_properties:
        variant_name = variant_name + block_property.name + "=" + block_property.value + ","
    mesh_name = obj.mcbde.block_type + "-" + variant_name[:-1]

    # Check if this model has already been created in the scene and reference it
    # However, we allow the object to refresh its own mesh
    for m in bpy.data.meshes:
        if m.name == mesh_name and m.name != obj.data.name:
            obj.data = m
            return
        
    if mesh_name not in [m.name for m in bpy.data.meshes]:
        # If this mesh does not exist, then we will need to create a new mesh
        obj.data = None
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj.data = mesh
    else:
        # If it does exist, we overwrite it
        bpy.ops.object.mode_set(mode='EDIT')
        mesh = bpy.context.edit_object.data
        bm = bmesh.from_edit_mesh(mesh)
        bmesh.ops.delete(bm, geom=bm.verts, context='VERTS')
        bmesh.update_edit_mesh(mesh)
        bpy.ops.object.mode_set(mode='OBJECT')

    obj.data.materials.clear()

    for model in outer_model_data:
        # If there are random variations, take the first one
        if isinstance(model, list):
            model = model[0]

        model_name = model["model"].split('/')[-1]

        model_data = data_loader.get_data("block_models", model_name)

        build_model(obj, model, model_data)