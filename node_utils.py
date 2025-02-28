import bpy
from bpy.types import Panel, Operator

def replace_node_with_type(node_tree, old_node, new_type):
    """
    Replace a node with a new node of specified type, preserving connections and position
    """
    # Debug prints for positions
    print("Old node original location:", old_node.location)
    print("Old node parent:", old_node.parent)
    if old_node.parent:
        print("Old node parent location:", old_node.parent.location)
    
    # Store the exact position and parent
    old_x = old_node.location.x
    old_y = old_node.location.y
    old_parent = old_node.parent
    old_offset_x = old_x - (old_parent.location.x if old_parent else 0)
    old_offset_y = old_y - (old_parent.location.y if old_parent else 0)
    
    # Store input connections
    input_links = []
    for input in old_node.inputs:
        if input.links:
            input_links.append({
                'name': input.name,
                'from_socket': input.links[0].from_socket,
                'from_node': input.links[0].from_node
            })
    
    # Store output connections
    output_links = []
    for output in old_node.outputs:
        for link in output.links:
            output_links.append({
                'name': output.name,
                'to_socket': link.to_socket,
                'to_node': link.to_node
            })
    
    # Create new node
    new_node = node_tree.nodes.new(type=new_type)
    print("New node initial location:", new_node.location)
    
    # Set parent first
    new_node.parent = old_parent
    
    # Set position relative to parent
    if old_parent:
        new_node.location.x = old_parent.location.x + old_offset_x
        new_node.location.y = old_parent.location.y + old_offset_y
    else:
        new_node.location.x = old_x
        new_node.location.y = old_y
    
    print("New node location after setting:", new_node.location)
    
    # Remove old node
    node_tree.nodes.remove(old_node)
    
    # Restore connections
    for link_info in input_links:
        for input in new_node.inputs:
            if input.name == link_info['name'] or input.type == link_info['from_socket'].type:
                node_tree.links.new(link_info['from_socket'], input)
                break
    
    # Restore output connections
    for link_info in output_links:
        for output in new_node.outputs:
            if output.name == link_info['name'] or output.type == link_info['to_socket'].type:
                node_tree.links.new(output, link_info['to_socket'])
                break
    
    # Final position check
    print("New node final location:", new_node.location)
    
    # Ensure the new node is selected and active
    for node in node_tree.nodes:
        node.select = False
    new_node.select = True
    node_tree.nodes.active = new_node
    
    return new_node

class NODEHELPER_MT_add_menu(bpy.types.Menu):
    bl_idname = "NODEHELPER_MT_add_menu"
    bl_label = "Add Node"
    
    def draw(self, context):
        layout = self.layout
        
        def add_node(node_type, text):
            op = layout.operator("nodehelper.finish_replace", text=text)
            op.node_type = node_type
        
        # Add common geometry nodes
        add_node('GeometryNodeTransform', "Transform")
        add_node('GeometryNodeSetPosition', "Set Position")
        add_node('GeometryNodeJoinGeometry', "Join Geometry")
        add_node('GeometryNodeMeshToPoints', "Mesh to Points")  
        # Add more nodes as needed

class NODEHELPER_OT_replace_node_with_menu(Operator):
    bl_idname = "nodehelper.replace_node_with_menu"
    bl_label = "Replace Node"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.space_data.type == 'NODE_EDITOR' and
                context.space_data.tree_type == 'GeometryNodeTree' and
                context.active_node is not None)
    
    def execute(self, context):
        if context.active_node:
            context.scene.stored_node_name = context.active_node.name
            bpy.ops.wm.call_menu(name="NODEHELPER_MT_add_menu")
        return {'FINISHED'}

class NODEHELPER_OT_finish_replace(Operator):
    bl_idname = "nodehelper.finish_replace"
    bl_label = "Internal Replace Node"
    bl_options = {'REGISTER', 'UNDO'}
    
    node_type: bpy.props.StringProperty()
    
    def execute(self, context):
        if context.scene.stored_node_name:
            node_tree = context.space_data.edit_tree
            old_node = node_tree.nodes.get(context.scene.stored_node_name)
            if old_node:
                replace_node_with_type(node_tree, old_node, self.node_type)
            context.scene.stored_node_name = ""
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
        
        row = box.row()
        row.scale_y = 1.5
        row.operator("nodehelper.replace_node_with_menu", text="Replace", icon='FILE_REFRESH')

classes = (
    NODEHELPER_OT_replace_node_with_menu,
    NODEHELPER_OT_finish_replace,
    NODEHELPER_PT_node,
    NODEHELPER_MT_add_menu,
)

def register():
    bpy.types.Scene.stored_node_name = bpy.props.StringProperty(
        name="Stored Node Name",
        description="Temporarily stores the name of the node being replaced",
        default=""
    )
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.stored_node_name

if __name__ == "__main__":
    register() 