import bpy
from bpy.types import Panel, Operator
from bpy.props import StringProperty, BoolProperty

class NODEHELPER_OT_hide_unused_sockets(Operator):
    bl_idname = "nodehelper.hide_unused_sockets"
    bl_label = "Hide Group Input Unused Sockets"
    bl_description = "Hide all unused sockets in the Group Input node"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.space_data.node_tree:
            for node in context.space_data.node_tree.nodes:
                if node.type == 'GROUP_INPUT':
                    for output in node.outputs:
                        if not output.links:
                            output.hide = True
        return {'FINISHED'}

class NODEHELPER_OT_jump_to_input(Operator):
    bl_idname = "nodehelper.jump_to_input"
    bl_label = "Jump to Input"
    bl_description = "Select the Group Input node and zoom to it"
    bl_options = {'REGISTER', 'UNDO'}

    input_name: StringProperty()

    def execute(self, context):
        if context.space_data.node_tree:
            for node in context.space_data.node_tree.nodes:
                if node.type == 'GROUP_INPUT':
                    context.space_data.node_tree.nodes.active = node
                    for output in node.outputs:
                        if output.name == self.input_name:
                            output.hide = False
                    bpy.ops.node.view_selected()
                    break
        return {'FINISHED'}

class NODEHELPER_PT_group_input(Panel):
    bl_label = "Group Input"
    bl_idname = "NODEHELPER_PT_group_input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "NodeHelper"

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR' and context.space_data.tree_type == 'GeometryNodeTree'

    def draw(self, context):
        layout = self.layout
        tree = context.space_data.node_tree

        # Group Input Operations
        box = layout.box()
        box.label(text="Group Input Operations")
        box.operator("nodehelper.hide_unused_sockets", text="Hide Unused Sockets")

        # Input Navigator
        box = layout.box()
        box.label(text="Input Navigator")
        
        if tree:
            group_input = next((node for node in tree.nodes if node.type == 'GROUP_INPUT'), None)
            if group_input:
                col = box.column()
                col.prop(context.scene, "input_search", text="Search")
                search_term = context.scene.input_search.lower()

                for output in group_input.outputs:
                    if search_term in output.name.lower():
                        row = col.row(align=True)
                        op = row.operator("nodehelper.jump_to_input", text=output.name)
                        op.input_name = output.name
                        row.label(text="", icon='RADIOBUT_ON' if not output.hide else 'RADIOBUT_OFF')

def register():
    bpy.utils.register_class(NODEHELPER_OT_hide_unused_sockets)
    bpy.utils.register_class(NODEHELPER_OT_jump_to_input)
    bpy.utils.register_class(NODEHELPER_PT_group_input)
    bpy.types.Scene.input_search = StringProperty(
        name="Input Search",
        description="Search for group inputs",
        default=""
    )

def unregister():
    bpy.utils.unregister_class(NODEHELPER_PT_group_input)
    bpy.utils.unregister_class(NODEHELPER_OT_jump_to_input)
    bpy.utils.unregister_class(NODEHELPER_OT_hide_unused_sockets)
    del bpy.types.Scene.input_search

if __name__ == "__main__":
    register()