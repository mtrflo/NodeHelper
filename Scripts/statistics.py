import bpy
import time

def get_node_execution_time(node):
    start_time = time.perf_counter()
    node.execute(None)
    end_time = time.perf_counter()
    return (end_time - start_time) * 1000  # Convert to milliseconds

def measure_nodes(scene):
    tree = bpy.context.space_data.edit_tree
    if not tree:
        return

    nodes_to_measure = ["Volume Cube", "String to Curves"]
    
    for node_name in nodes_to_measure:
        node = tree.nodes.get(node_name)
        if node:
            execution_time = get_node_execution_time(node)
            print(f"Frame {scene.frame_current}, {node_name}: {execution_time:.4f} ms")

class NODEHELPER_OT_toggle_timing(bpy.types.Operator):
    bl_idname = "nodehelper.toggle_timing"
    bl_label = "Toggle Node Timing"
    bl_description = "Toggle node execution time measurement"

    def execute(self, context):
        if measure_nodes in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(measure_nodes)
            self.report({'INFO'}, "Node timing stopped")
        else:
            bpy.app.handlers.frame_change_post.append(measure_nodes)
            self.report({'INFO'}, "Node timing started")
        return {'FINISHED'}

class NODEHELPER_PT_main(bpy.types.Panel):
    bl_label = "NodeHelper"
    bl_idname = "NODEHELPER_PT_main"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "NodeHelper"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        if measure_nodes in bpy.app.handlers.frame_change_post:
            row.operator("nodehelper.toggle_timing", text="Stop Node Timing")
        else:
            row.operator("nodehelper.toggle_timing", text="Start Node Timing")

classes = (
    NODEHELPER_OT_toggle_timing,
    NODEHELPER_PT_main
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if measure_nodes in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(measure_nodes)

if __name__ == "__main__":
    register()