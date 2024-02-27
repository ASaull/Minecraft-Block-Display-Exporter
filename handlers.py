

def on_object_deleted(scene):
    deleted_objects = bpy.context.window_manager.event_queue.pop()

    for obj in deleted_objects:
        if obj.mcbde.block_type != "":
            