import bpy
from bpy.types import Operator, Panel

class NODEHELPER_OT_jump_to_connected_node(Operator):
    bl_idname = "nodehelper.jump_to_connected_node"
    bl_label = "Jump to Connected Node"
    bl_description = "Jump to the nodes using this input"
    bl_options = {'REGISTER', 'UNDO'}

    input_name: bpy.props.StringProperty()

    def find_nodes_using_input(self, tree, input_name):
        nodes = []
        for node in tree.nodes:
            if node.type == 'GROUP_INPUT':
                continue
            for input_socket in node.inputs:
                if input_socket.links:
                    from_socket = input_socket.links[0].from_socket
                    if from_socket.node.type == 'GROUP_INPUT' and from_socket.name == input_name:
                        nodes.append(node)
                        break  # Break to avoid adding the same node multiple times
        return nodes

    def execute(self, context):
        active_tree = context.space_data.edit_tree
        if not active_tree:
            self.report({'WARNING'}, "No active node tree")
            return {'CANCELLED'}

        connected_nodes = self.find_nodes_using_input(active_tree, self.input_name)
        if not connected_nodes:
            self.report({'WARNING'}, f"No nodes found using input: {self.input_name}")
            return {'CANCELLED'}

        # Get the current index and increment it
        current_index = context.scene.nodehelper_current_node_index
        next_index = (current_index + 1) % len(connected_nodes)
        context.scene.nodehelper_current_node_index = next_index

        # Select and focus on the next connected node
        for node in active_tree.nodes:
            node.select = False
        
        connected_node = connected_nodes[next_index]
        connected_node.select = True
        active_tree.nodes.active = connected_node

        # Center view on the node
        bpy.ops.node.view_selected()

        self.report({'INFO'}, f"Jumped to node {next_index + 1}/{len(connected_nodes)} using input: {self.input_name}")
        return {'FINISHED'}

class NODEHELPER_PT_input_navigator(Panel):
    bl_label = "Input Navigator"
    bl_idname = "NODEHELPER_PT_input_navigator"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "NodeHelper"

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR'

    def draw(self, context):
        layout = self.layout
        active_tree = context.space_data.edit_tree

        if not active_tree:
            layout.label(text="No active node tree")
            return

        group_input = next((node for node in active_tree.nodes if node.type == 'GROUP_INPUT'), None)
        if not group_input:
            layout.label(text="No Group Input node found")
            return

        layout.label(text="Group Inputs:")
        
        # Add search field
        layout.prop(context.scene, "nodehelper_input_search", text="Search")
        search_term = context.scene.nodehelper_input_search.lower()

        # Filter out empty inputs and draw valid ones
        for input_socket in group_input.outputs:
            # Skip empty or invalid inputs
            if not input_socket.name or input_socket.name.isspace():
                continue
            
            if search_term and search_term not in input_socket.name.lower():
                continue
            
            row = layout.row(align=True)
            row.label(text=input_socket.name)
            op = row.operator("nodehelper.jump_to_connected_node", text="", icon='VIEWZOOM')
            op.input_name = input_socket.name

def register():
    bpy.utils.register_class(NODEHELPER_OT_jump_to_connected_node)
    bpy.utils.register_class(NODEHELPER_PT_input_navigator)
    bpy.types.Scene.nodehelper_input_search = bpy.props.StringProperty(
        name="Search Input",
        description="Search for specific group inputs"
    )
    bpy.types.Scene.nodehelper_current_node_index = bpy.props.IntProperty(
        name="Current Node Index",
        default=0,
        min=0
    )

def unregister():
    bpy.utils.unregister_class(NODEHELPER_PT_input_navigator)
    bpy.utils.unregister_class(NODEHELPER_OT_jump_to_connected_node)
    del bpy.types.Scene.nodehelper_input_search
    del bpy.types.Scene.nodehelper_current_node_index

if __name__ == "__main__":
    register()