import bpy

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


def reselect(prev):
    """
    Reselects all the objects in prev

    Usage:
    prev = deselect_all_except(obj)
    Do Stuff
    reselect(prev)

    Args:
        prev: a list of previously selected objects, as returned by deselect_all_except()
    """
    bpy.ops.object.select_all(action='DESELECT')
    for obj in prev:
        obj.select_set(True)