import bpy
from bpy.types import Panel, Operator
from bpy.props import StringProperty, IntProperty

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




class NODEHELPER_OT_drag_input(Operator):
    bl_idname = "nodehelper.drag_input"
    bl_label = "Drag Input"
    bl_description = "Click to add a Group Input node for this input and drag to position it"
    bl_options = {'REGISTER', 'UNDO'}

    input_name: StringProperty()

    def invoke(self, context, event):
        tree = context.space_data.node_tree
        if not tree:
            return {'CANCELLED'}

        # Create a new Group Input node at the mouse position
        mouse_x, mouse_y = context.region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
        input_node = tree.nodes.new(type='NodeGroupInput')
        input_node.location = mouse_x, mouse_y

        # Hide all outputs except the one we want
        for output in input_node.outputs:
            if output.name == self.input_name:
                output.hide = False
            else:
                output.hide = True

        # Select and make the new node active
        for node in tree.nodes:
            node.select = False
        input_node.select = True
        tree.nodes.active = input_node

        # Start the grab operation
        bpy.ops.transform.translate('INVOKE_DEFAULT')

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

class NODEHELPER_OT_jump_to_connected_node(Operator):
    bl_idname = "nodehelper.jump_to_connected_node"
    bl_label = "Jump to Connected Node"
    bl_description = "Jump to the nodes using this input"
    bl_options = {'REGISTER', 'UNDO'}

    input_name: StringProperty()

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
                col.prop(context.scene, "nodehelper_input_search", text="Search")
                search_term = context.scene.nodehelper_input_search.lower()

                for output in group_input.outputs:
                    # Skip outputs without a name
                    if not output.name:
                        continue
                    
                    if search_term in output.name.lower():
                        row = col.row(align=True)
                        row.scale_y = 1.5  # This makes the buttons 1.5 times as tall
                        
                        # Drag and drop button
                        split = row.split(factor=0.8)
                        op = split.operator("nodehelper.drag_input", text=output.name)
                        op.input_name = output.name
                        
                        # Jump to connected node button (wider than before)
                        op = split.operator("nodehelper.jump_to_connected_node", text="", icon='VIEWZOOM')
                        op.input_name = output.name
                        
                        # Add a small vertical space between buttons
                        col.separator(factor=0.2)

def register():
    bpy.utils.register_class(NODEHELPER_OT_hide_unused_sockets)
    bpy.utils.register_class(NODEHELPER_OT_jump_to_input)
    bpy.utils.register_class(NODEHELPER_OT_jump_to_connected_node)
    bpy.utils.register_class(NODEHELPER_OT_drag_input)  # Add this line
    bpy.utils.register_class(NODEHELPER_PT_group_input)
    bpy.types.Scene.nodehelper_input_search = StringProperty(
        name="Input Search",
        description="Search for group inputs",
        default=""
    )
    bpy.types.Scene.nodehelper_current_node_index = IntProperty(
        name="Current Node Index",
        default=0,
        min=0
    )

def unregister():
    bpy.utils.unregister_class(NODEHELPER_PT_group_input)
    bpy.utils.unregister_class(NODEHELPER_OT_drag_input)  # Add this line
    bpy.utils.unregister_class(NODEHELPER_OT_jump_to_connected_node)
    bpy.utils.unregister_class(NODEHELPER_OT_jump_to_input)
    bpy.utils.unregister_class(NODEHELPER_OT_hide_unused_sockets)
    del bpy.types.Scene.nodehelper_input_search
    del bpy.types.Scene.nodehelper_current_node_index

if __name__ == "__main__":
    register()