import bpy
from bpy.types import Panel, Operator

class NODEHELPER_OT_select_group_inputs_hide_sockets(Operator):
    bl_idname = "nodehelper.select_group_inputs_hide_sockets"
    bl_label = "Hide Group Input Unused Sockets"
    bl_description = "Select all Group Input nodes and hide unconnected sockets in the current node group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.space_data.type != 'NODE_EDITOR':
            self.report({'WARNING'}, "This operator only works in the Node Editor")
            return {'CANCELLED'}

        active_tree = context.space_data.edit_tree
        if not active_tree:
            self.report({'WARNING'}, "No active node tree")
            return {'CANCELLED'}

        # Process only the active node tree
        group_inputs_processed = False
        for node in active_tree.nodes:
            if node.type == 'GROUP_INPUT':
                node.select = True
                for output in node.outputs:
                    if not output.links:
                        output.hide = True
                group_inputs_processed = True

        if group_inputs_processed:
            self.report({'INFO'}, "Processed Group Input nodes in the current node group")
        else:
            self.report({'WARNING'}, "No Group Input nodes found in the current node group")

        return {'FINISHED'}


class NODEHELPER_PT_general(Panel):
    bl_label = "General"
    bl_idname = "NODEHELPER_PT_general"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "NodeHelper"

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR'

    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Group Input Operations")
        
        # Create a column with scale_y set to 2 for double height
        col = layout.column()
        col.scale_y = 2
        
        # Add the operator button to this column
        col.operator("nodehelper.select_group_inputs_hide_sockets")

def register():
    bpy.utils.register_class(NODEHELPER_OT_select_group_inputs_hide_sockets)
    bpy.utils.register_class(NODEHELPER_PT_general)

def unregister():
    bpy.utils.unregister_class(NODEHELPER_PT_general)
    bpy.utils.unregister_class(NODEHELPER_OT_select_group_inputs_hide_sockets)

if __name__ == "__main__":
    register()