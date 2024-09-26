import bpy
from bpy.types import Operator, PropertyGroup, Panel
from bpy.props import StringProperty, CollectionProperty, IntProperty, BoolProperty

class FoundAttribute(PropertyGroup):
    node_path: StringProperty(name="Node Path")
    node_name: StringProperty(name="Node Name")

class NODEHELPER_OT_find_named_attributes(Operator):
    bl_idname = "nodehelper.find_named_attributes"
    bl_label = "Find Named Attributes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.area.type != 'NODE_EDITOR':
            self.report({'ERROR'}, "This operator must be used in the Node Editor.")
            return {'CANCELLED'}

        search_name = context.scene.attribute_search_name.lower()
        node_tree = context.space_data.node_tree
        
        if not node_tree or node_tree.type != 'GEOMETRY':
            self.report({'ERROR'}, "No active Geometry Node tree found.")
            return {'CANCELLED'}
        
        context.scene.found_attributes.clear()
        
        def search_node(node, path, tree):
            if hasattr(node, 'node_tree'):
                for sub_node in node.node_tree.nodes:
                    search_node(sub_node, path + [node.name], node.node_tree)
            
            if "Named Attribute" in node.bl_label:
                if hasattr(node, 'attribute_name'):
                    attribute_name = node.attribute_name.lower()
                elif hasattr(node, 'inputs') and len(node.inputs) > 0 and hasattr(node.inputs[0], 'default_value'):
                    attribute_name = node.inputs[0].default_value.lower()
                else:
                    attribute_name = node.name.lower()

                if search_name in attribute_name:
                    item = context.scene.found_attributes.add()
                    item.node_path = ' > '.join(path + [node.name])
                    item.node_name = node.name

        for node in node_tree.nodes:
            search_node(node, [], node_tree)
        
        return {'FINISHED'}

class NODEHELPER_OT_jump_to_node(Operator):
    bl_idname = "nodehelper.jump_to_node"
    bl_label = "Jump to Node"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty()

    def execute(self, context):
        item = context.scene.found_attributes[self.index]
        path = item.node_path.split(' > ')
        target_node_name = path[-1]

        current_tree = context.space_data.node_tree
        context.space_data.path.clear()
        context.space_data.path.start(current_tree)

        for i, node_name in enumerate(path):
            node = current_tree.nodes.get(node_name)
            if not node:
                self.report({'ERROR'}, f"Node '{node_name}' not found.")
                return {'CANCELLED'}

            for n in current_tree.nodes:
                n.select = False
            node.select = True
            current_tree.nodes.active = node

            if i == len(path) - 1:
                bpy.ops.node.view_selected('INVOKE_DEFAULT')
                for area in context.screen.areas:
                    if area.type == 'NODE_EDITOR':
                        area.tag_redraw()
                self.report({'INFO'}, f"Jumped to node: {node.name}")
                return {'FINISHED'}
            else:
                if node.type == 'GROUP' and node.node_tree:
                    bpy.ops.node.group_edit('INVOKE_DEFAULT')
                    current_tree = node.node_tree
                else:
                    self.report({'ERROR'}, f"Node '{node_name}' is not a valid group.")
                    return {'CANCELLED'}

        self.report({'ERROR'}, "Failed to navigate to the target node.")
        return {'CANCELLED'}

class NODEHELPER_PT_find_panel(Panel):
    bl_label = "Find Attribute Nodes"
    bl_idname = "NODEHELPER_PT_find_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "NodeHelper"

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR' and context.space_data.tree_type == 'GeometryNodeTree'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "attribute_search_name", text="Search")
        layout.operator("nodehelper.find_named_attributes", text="Find Attributes")

        # Create a box to contain the list
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_attribute_list", icon="TRIA_DOWN" if scene.show_attribute_list else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Found Attributes")

        # If the list is expanded, show the scrollable list
        if scene.show_attribute_list:
            row = box.row()
            col = row.column()
            col.template_list("NODEHELPER_UL_AttributeList", "", scene, "found_attributes", scene, "active_attribute_index", rows=5)

# Custom list class
class NODEHELPER_UL_AttributeList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.label(text=item.node_path)
            op = row.operator("nodehelper.jump_to_node", text="", icon='VIEWZOOM', emboss=False)
            op.index = data.found_attributes.values().index(item)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='NODE')

def register():
    bpy.utils.register_class(FoundAttribute)
    bpy.utils.register_class(NODEHELPER_OT_find_named_attributes)
    bpy.utils.register_class(NODEHELPER_OT_jump_to_node)
    bpy.utils.register_class(NODEHELPER_PT_find_panel)
    bpy.utils.register_class(NODEHELPER_UL_AttributeList)
    bpy.types.Scene.found_attributes = CollectionProperty(type=FoundAttribute)
    bpy.types.Scene.attribute_search_name = StringProperty(
        name="Search Attribute",
        description="Enter the name of the attribute to search for",
        default=""
    )
    bpy.types.Scene.show_attribute_list = BoolProperty(
        name="Show Attribute List",
        default=True
    )
    bpy.types.Scene.active_attribute_index = IntProperty()

def unregister():
    del bpy.types.Scene.active_attribute_index
    del bpy.types.Scene.show_attribute_list
    del bpy.types.Scene.attribute_search_name
    del bpy.types.Scene.found_attributes
    bpy.utils.unregister_class(NODEHELPER_UL_AttributeList)
    bpy.utils.unregister_class(NODEHELPER_PT_find_panel)
    bpy.utils.unregister_class(NODEHELPER_OT_jump_to_node)
    bpy.utils.unregister_class(NODEHELPER_OT_find_named_attributes)
    bpy.utils.unregister_class(FoundAttribute)

if __name__ == "__main__":
    register()