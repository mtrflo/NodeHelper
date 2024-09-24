import bpy
from bpy.types import Operator

print("NodeHelper addon loaded - Version 2.1")

class NODEHELPER_OT_rename_attribute(Operator):
    bl_idname = "nodehelper.rename_attribute"
    bl_label = "Rename Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print("Rename attribute operator executed - Version 2.1")
        old_name = context.scene.old_attribute_name
        new_name = context.scene.new_attribute_name
        print(f"Attempting to rename from '{old_name}' to '{new_name}'")
        
        # Ensure there is an edit_tree in the space_data
        if context.space_data and hasattr(context.space_data, 'edit_tree') and context.space_data.edit_tree:
            self.rename_attributes_recursive(context.space_data.edit_tree, old_name, new_name)
        else:
            self.report({'WARNING'}, "No node tree found in the current space.")
        
        return {'FINISHED'}

    def rename_attributes_recursive(self, node_tree, old_name, new_name):
        for node in node_tree.nodes:
            print(f"Checking node: {node.name}, Type: {node.bl_idname}")
            
            # Rename Store Named Attribute nodes
            if node.bl_idname == 'GeometryNodeStoreNamedAttribute':
                self.rename_store_named_attribute(node, old_name, new_name)
            
            # Rename Input Named Attribute nodes
            elif node.bl_idname == 'GeometryNodeInputNamedAttribute':
                self.rename_input_named_attribute(node, old_name, new_name)
            
            # Rename the node's own name if it matches old_name
            if node.name == old_name:
                node.name = new_name
                print(f"Renamed node name from '{old_name}' to '{new_name}'")
        
            # If the node is a group, recurse into its node tree
            if node.type == 'GROUP' and node.node_tree:
                print(f"Entering group node: {node.name}")
                self.rename_attributes_recursive(node.node_tree, old_name, new_name)

    def rename_store_named_attribute(self, node, old_name, new_name):
        renamed = False
        for input_socket in node.inputs:
            if input_socket.name == 'Name' and input_socket.default_value == old_name:
                input_socket.default_value = new_name
                renamed = True
                print(f"Renamed Store Named Attribute: {node.name} from '{old_name}' to '{new_name}'")
        return renamed

    def rename_input_named_attribute(self, node, old_name, new_name):
        if node.inputs and node.inputs[0].default_value == old_name:
            node.inputs[0].default_value = new_name
            print(f"Renamed Input Named Attribute: {node.name} from '{old_name}' to '{new_name}'")

def register():
    bpy.utils.register_class(NODEHELPER_OT_rename_attribute)
    # Add properties to the Scene if not already present
    if not hasattr(bpy.types.Scene, 'old_attribute_name'):
        bpy.types.Scene.old_attribute_name = bpy.props.StringProperty(
            name="Old Attribute Name",
            description="Name of the attribute to rename",
            default=""
        )
    if not hasattr(bpy.types.Scene, 'new_attribute_name'):
        bpy.types.Scene.new_attribute_name = bpy.props.StringProperty(
            name="New Attribute Name",
            description="New name for the attribute",
            default=""
        )

def unregister():
    bpy.utils.unregister_class(NODEHELPER_OT_rename_attribute)
    # Remove properties from the Scene
    del bpy.types.Scene.old_attribute_name
    del bpy.types.Scene.new_attribute_name

if __name__ == "__main__":
    register()