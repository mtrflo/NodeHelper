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
    bl_order = 2
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

class NODEHELPER_OT_rename_attribute(Operator):
    bl_idname = "nodehelper.rename_attribute"
    bl_label = "Rename Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        old_name = context.scene.old_attribute_name
        new_name = context.scene.new_attribute_name

        if not old_name or not new_name:
            self.report({'ERROR'}, "Both old and new names must be provided.")
            return {'CANCELLED'}

        # Get all node groups in the file
        node_groups = [ng for ng in bpy.data.node_groups if ng.type == 'GEOMETRY']

        renamed_count = 0
        for ng in node_groups:
            renamed_count += self.rename_attributes_in_tree(ng, old_name, new_name)

        self.report({'INFO'}, f"Renamed {renamed_count} attribute(s) from '{old_name}' to '{new_name}'.")
        return {'FINISHED'}

    def rename_attributes_in_tree(self, node_tree, old_name, new_name):
        renamed_count = 0
        for node in node_tree.nodes:
            if node.bl_idname == 'GeometryNodeStoreNamedAttribute':
                renamed_count += self.rename_store_named_attribute(node, old_name, new_name)
            elif node.bl_idname == 'GeometryNodeInputNamedAttribute':
                renamed_count += self.rename_input_named_attribute(node, old_name, new_name)
            
            if node.name == old_name:
                node.name = new_name
                renamed_count += 1
        
        return renamed_count

    def rename_store_named_attribute(self, node, old_name, new_name):
        renamed = 0
        for input_socket in node.inputs:
            if input_socket.name == 'Name' and input_socket.default_value == old_name:
                input_socket.default_value = new_name
                renamed += 1
        return renamed

    def rename_input_named_attribute(self, node, old_name, new_name):
        if node.inputs and node.inputs[0].default_value == old_name:
            node.inputs[0].default_value = new_name
            return 1
        return 0

class NODEHELPER_PT_attribute_panel(Panel):
    bl_label = "Attribute"
    bl_idname = "NODEHELPER_PT_attribute_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "NodeHelper"

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR' and context.space_data.tree_type == 'GeometryNodeTree'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Rename Attribute section
        box = layout.box()
        box.label(text="Rename")
        box.prop(scene, "old_attribute_name", text="Old Name")
        box.prop(scene, "new_attribute_name", text="New Name")
        box.operator("nodehelper.rename_attribute", text="Rename")

        # Find Attribute Nodes section
        box = layout.box()
        box.label(text="Find")
        box.prop(scene, "attribute_search_name", text="Search")
        box.operator("nodehelper.find_named_attributes", text="Find Attributes")

        # Found Attributes list
        row = box.row()
        row.prop(scene, "show_attribute_list", icon="TRIA_DOWN" if scene.show_attribute_list else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Found Attributes")

        if scene.show_attribute_list:
            row = box.row()
            col = row.column()
            col.template_list("NODEHELPER_UL_AttributeList", "", scene, "found_attributes", scene, "active_attribute_index", rows=5)

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
    bpy.utils.register_class(NODEHELPER_OT_rename_attribute)
    bpy.utils.register_class(NODEHELPER_PT_attribute_panel)
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
    bpy.types.Scene.old_attribute_name = StringProperty(name="Old Attribute Name")
    bpy.types.Scene.new_attribute_name = StringProperty(name="New Attribute Name")

def unregister():
    del bpy.types.Scene.new_attribute_name
    del bpy.types.Scene.old_attribute_name
    del bpy.types.Scene.active_attribute_index
    del bpy.types.Scene.show_attribute_list
    del bpy.types.Scene.attribute_search_name
    del bpy.types.Scene.found_attributes
    bpy.utils.unregister_class(NODEHELPER_UL_AttributeList)
    bpy.utils.unregister_class(NODEHELPER_PT_attribute_panel)
    bpy.utils.unregister_class(NODEHELPER_OT_rename_attribute)
    bpy.utils.unregister_class(NODEHELPER_OT_jump_to_node)
    bpy.utils.unregister_class(NODEHELPER_OT_find_named_attributes)
    bpy.utils.unregister_class(FoundAttribute)

if __name__ == "__main__":
    register()