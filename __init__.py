bl_info = {
    "name": "Minecraft Block Display Exporter (MCBDE)",
    "author": "Aidan Saull",
    "version": (0, 1, 0),
    "blender": (4, 00, 0),
    "location": "View3D > UI > MCBDE",
    "description": "Allows exporting Blender cubes as Minecraft block displays.",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

import bpy
import mathutils
from . import operators
from . import properties
from . import interface

def register():
    properties.register()
    interface.register()
    operators.register()


def unregister():
    interface.unregister()
    operators.unregister()
    properties.unregister()