import bpy
from bpy.types import Operator


class NODEHELPER_OT_rename_attribute(Operator):
    bl_idname = "nodehelper.rename_attribute"
    bl_label = "Rename Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR' and context.space_data.edit_tree is not None

    def execute(self, context):
        old_name = context.scene.old_attribute_name
        new_name = context.scene.new_attribute_name

        if not old_name or not new_name:
            self.report({'ERROR'}, "Both old and new names must be provided.")
            return {'CANCELLED'}

        node_tree = context.space_data.edit_tree
        if not node_tree:
            self.report({'ERROR'}, "No active node tree found.")
            return {'CANCELLED'}

        count = self.rename_attributes_recursive(node_tree, old_name, new_name)
        
        if count > 0:
            self.report({'INFO'}, f"Renamed {count} Named Attribute nodes.")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, f"No Named Attribute nodes with name '{old_name}' found.")
            return {'CANCELLED'}

    def rename_attributes_recursive(self, node_tree, old_name, new_name):
        count = 0
        for node in node_tree.nodes:
            if node.type == 'GROUP' and node.node_tree:
                count += self.rename_attributes_recursive(node.node_tree, old_name, new_name)
            
            if node.bl_idname == 'GeometryNodeInputNamedAttribute' and node.inputs[0].default_value == old_name:
                node.inputs[0].default_value = new_name
                count += 1
        
        return count


def register():
    bpy.utils.register_class(NODEHELPER_OT_rename_attribute)

def unregister():
    bpy.utils.unregister_class(NODEHELPER_OT_rename_attribute)