import bpy
from bpy.types import Panel, Operator

def replace_node_with_type(node_tree, old_node, new_type):
    # Store the exact position and parent
    old_x, old_y = old_node.location.x, old_node.location.y
    old_parent = old_node.parent
    old_offset_x = old_x - (old_parent.location.x if old_parent else 0)
    old_offset_y = old_y - (old_parent.location.y if old_parent else 0)
    
    # Store input/output connections
    input_links = []
    for input in old_node.inputs:
        if input.links:
            input_links.append({
                'name': input.name,
                'from_socket': input.links[0].from_socket,
                'from_node': input.links[0].from_node
            })
    
    output_links = []
    for output in old_node.outputs:
        for link in output.links:
            output_links.append({
                'name': output.name,
                'to_socket': link.to_socket,
                'to_node': link.to_node
            })
    
    # Create new node
    try:
        new_node = node_tree.nodes.new(type=new_type)
    except RuntimeError as e:
        return None
    
    # Set parent and position
    new_node.parent = old_parent
    new_node.location.x = old_x if not old_parent else old_parent.location.x + old_offset_x
    new_node.location.y = old_y if not old_parent else old_parent.location.y + old_offset_y
    
    # Remove old node
    node_tree.nodes.remove(old_node)
    
    # Restore connections
    for link_info in input_links:
        for input in new_node.inputs:
            if input.name == link_info['name'] or input.type == link_info['from_socket'].type:
                node_tree.links.new(link_info['from_socket'], input)
                break
    
    for link_info in output_links:
        for output in new_node.outputs:
            if output.name == link_info['name'] or output.type == link_info['to_socket'].type:
                node_tree.links.new(output, link_info['to_socket'])
                break
    
    # Select new node
    for node in node_tree.nodes:
        node.select = False
    new_node.select = True
    node_tree.nodes.active = new_node
    
    return new_node


class NODEHELPER_OT_replace_with_selected(bpy.types.Operator):
    bl_idname = "nodehelper.replace_with_selected"
    bl_label = "Replace With Selected"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        if not (context.space_data.type == 'NODE_EDITOR' and
                context.space_data.tree_type == 'GeometryNodeTree'):
            return False
        # Check if we have exactly two nodes selected
        selected_nodes = [n for n in context.space_data.edit_tree.nodes if n.select]
        return len(selected_nodes) == 2
    
    def execute(self, context):
        # Get selected nodes
        selected_nodes = [n for n in context.space_data.edit_tree.nodes if n.select]
        if len(selected_nodes) != 2:
            self.report({'ERROR'}, "Please select exactly two nodes")
            return {'CANCELLED'}
        
        # First selected node will be replaced with type of second selected node
        node_to_replace = selected_nodes[0]
        node_type_source = selected_nodes[1]
        
        # Replace the node
        replace_node_with_type(context.space_data.edit_tree, node_to_replace, node_type_source.bl_idname)
        
        # Always remove the second node
        context.space_data.edit_tree.nodes.remove(node_type_source)
        
        return {'FINISHED'}

class NODEHELPER_OT_start_node_replacement(Operator):
    bl_idname = "nodehelper.start_node_replacement"
    bl_label = "Replace Node"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.space_data.type == 'NODE_EDITOR' and
                context.space_data.tree_type == 'GeometryNodeTree' and
                len([n for n in context.space_data.edit_tree.nodes if n.select]) == 1)

    def execute(self, context):
        # Save the selected node
        selected_nodes = [n for n in context.space_data.edit_tree.nodes if n.select]
        if len(selected_nodes) != 1:
            self.report({'ERROR'}, "Please select exactly one node to replace")
            return {'CANCELLED'}
            
        # Store the node to replace
        context.scene.nodehelper_node_to_replace = selected_nodes[0].name
        
        # Enable the listener for new nodes
        context.scene.nodehelper_listening_for_new_node = True
        
        # Open add menu
        bpy.ops.wm.call_menu(name="NODE_MT_add")
        
        return {'FINISHED'}

class NODEHELPER_OT_cancel_replacement(Operator):
    bl_idname = "nodehelper.cancel_replacement"
    bl_label = "Cancel Replacement"
    
    def execute(self, context):
        context.scene.nodehelper_listening_for_new_node = False
        context.scene.nodehelper_node_to_replace = ""
        return {'FINISHED'}

class NODEHELPER_PT_node(Panel):
    bl_label = "Node"
    bl_idname = "NODEHELPER_PT_node"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "NodeHelper"
    
    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR' and context.space_data.tree_type == 'GeometryNodeTree'
    
    def draw(self, context):
        layout = self.layout
        
        # Node Operations
        box = layout.box()
        box.label(text="Node Operations")
        
        if context.scene.nodehelper_listening_for_new_node:
            row = box.row(align=True)
            row.alert = True
            row.label(text="Select new node type...", icon='INFO')
            row = box.row()
            row.operator("nodehelper.cancel_replacement", text="Cancel", icon='X')
        else:
            row = box.row()
            row.scale_y = 1.5
            row.operator("nodehelper.start_node_replacement", text="Replace Node", icon='FILE_REFRESH')

def node_handler(scene):
    if not scene.nodehelper_listening_for_new_node:
        return
    
    context = bpy.context
    tree = context.space_data.edit_tree
    if not tree:
        return
    
    new_nodes = [n for n in tree.nodes if n.select]
    
    if len(new_nodes) == 1:
        new_node = new_nodes[0]
        
        old_node = tree.nodes.get(scene.nodehelper_node_to_replace)
        if old_node:
            replace_node_with_type(tree, old_node, new_node.bl_idname)
            
            # Always remove the source node
            tree.nodes.remove(new_node)
        
        scene.nodehelper_listening_for_new_node = False
        scene.nodehelper_node_to_replace = ""

classes = (
    NODEHELPER_OT_replace_with_selected,
    NODEHELPER_OT_start_node_replacement,
    NODEHELPER_OT_cancel_replacement,
    NODEHELPER_PT_node,
)

def register():
    bpy.types.Scene.nodehelper_listening_for_new_node = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.nodehelper_node_to_replace = bpy.props.StringProperty(default="")
    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.app.handlers.depsgraph_update_post.append(node_handler)

def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(node_handler)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.nodehelper_listening_for_new_node
    del bpy.types.Scene.nodehelper_node_to_replace