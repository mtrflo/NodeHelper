import bpy
from bpy.types import Panel, Operator

class NODEHELPER_OT_set_frame_color(Operator):
    bl_idname = "nodehelper.set_frame_color"
    bl_label = "Set Dark Frame Color"
    bl_description = "Set selected frame node color to dark gray"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        space = context.space_data
        active_tree = space.edit_tree or space.node_tree
        
        if active_tree:
            for node in active_tree.nodes:
                if node.select and node.type == 'FRAME':
                    node.use_custom_color = True
                    node.color = (0.3, 0.3, 0.3)
        
        return {'FINISHED'}

class NODEHELPER_OT_increase_label_size(Operator):
    bl_idname = "nodehelper.increase_label_size"
    bl_label = "Bigger Label Size"
    bl_description = "Increase label size of selected frames by 10"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        space = context.space_data
        active_tree = space.edit_tree or space.node_tree
        
        if active_tree:
            for node in active_tree.nodes:
                if node.select and node.type == 'FRAME':
                    node.label_size += 10
        
        return {'FINISHED'}

class NODEHELPER_PT_frame(Panel):
    bl_label = "Frame"
    bl_idname = "NODEHELPER_PT_frame"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "NodeHelper"

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR' and context.space_data.tree_type == 'GeometryNodeTree'

    def draw(self, context):
        layout = self.layout
        
        # Frame Operations
        box = layout.box()
        box.label(text="Frame Operations")
        
        # Make the buttons 1.5 times bigger
        row = box.row()
        row.scale_y = 1.5
        row.operator("nodehelper.increase_label_size", text="Bigger Label Size")
        
        row = box.row()
        row.scale_y = 1.5
        row.operator("nodehelper.set_frame_color", text="Set Dark Frame Color")

def register():
    bpy.utils.register_class(NODEHELPER_OT_set_frame_color)
    bpy.utils.register_class(NODEHELPER_OT_increase_label_size)
    bpy.utils.register_class(NODEHELPER_PT_frame)

def unregister():
    bpy.utils.unregister_class(NODEHELPER_PT_frame)
    bpy.utils.unregister_class(NODEHELPER_OT_increase_label_size)
    bpy.utils.unregister_class(NODEHELPER_OT_set_frame_color)

if __name__ == "__main__":
    register() 