import bpy
from bpy.types import Operator, PropertyGroup, Panel
from bpy.props import StringProperty, CollectionProperty, IntProperty, BoolProperty

class FoundAttribute(PropertyGroup):
    node_path: StringProperty(name="Node Path")
    node_name: StringProperty(name="Node Name")
    hierarchy_level: IntProperty(name="Hierarchy Level")

class NODEHELPER_OT_find_named_attributes(Operator):
    bl_idname = "nodehelper.find_named_attributes"
    bl_label = "Find Named Attributes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.area.type != 'NODE_EDITOR':
            self.report({'ERROR'}, "This operator must be used in the Node Editor.")
            return {'CANCELLED'}

        search_name = context.scene.attribute_search_name.lower()
        
        context.scene.found_attributes.clear()
        
        found_nodes = set()

        for node_group in bpy.data.node_groups:
            if node_group.type == 'GEOMETRY':
                self.search_node_tree(node_group, search_name, [], found_nodes)

        self.report({'INFO'}, f"Found {len(context.scene.found_attributes)} unique attribute node(s).")
        return {'FINISHED'}

    def search_node_tree(self, node_tree, search_name, path, found_nodes, hierarchy_level=0):
        for node in node_tree.nodes:
            if node.type == 'GROUP' and node.node_tree:
                current_path = path + [f"{node.node_tree.name} (Group)"]
                self.search_node_tree(node.node_tree, search_name, current_path, found_nodes, hierarchy_level + 1)
            else:
                current_path = path + [node.name]
            
            if node.bl_idname in ['GeometryNodeInputNamedAttribute', 'GeometryNodeStoreNamedAttribute', 'GeometryNodeRemoveNamedAttribute']:
                attribute_name = self.get_attribute_name(node)
                if search_name in attribute_name.lower():
                    if node not in found_nodes:
                        self.add_found_attribute(node, current_path, attribute_name, hierarchy_level)
                        found_nodes.add(node)

    def get_attribute_name(self, node):
        if node.bl_idname == 'GeometryNodeInputNamedAttribute':
            return node.inputs[0].default_value
        elif node.bl_idname == 'GeometryNodeStoreNamedAttribute':
            name_socket = next((input for input in node.inputs if input.name == 'Name'), None)
            return name_socket.default_value if name_socket else node.name
        elif node.bl_idname == 'GeometryNodeRemoveNamedAttribute':
            return node.inputs[1].default_value
        return node.name

    def add_found_attribute(self, node, path, attribute_name, hierarchy_level):
        item = bpy.context.scene.found_attributes.add()
        item.node_path = ' > '.join(path)
        item.node_name = f"{node.bl_label}: {attribute_name}"
        item.hierarchy_level = hierarchy_level

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
            if " (Group)" in node_name:
                group_name = node_name.split(" (Group)")[0]
                node = next((n for n in current_tree.nodes if n.type == 'GROUP' and n.node_tree and n.node_tree.name == group_name), None)
            else:
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

        renamed_count = self.rename_attributes(old_name, new_name)

        self.report({'INFO'}, f"Renamed {renamed_count} attribute(s) from '{old_name}' to '{new_name}'.")
        
        for area in bpy.context.screen.areas:
            if area.type == 'NODE_EDITOR':
                area.tag_redraw()
        
        return {'FINISHED'}

    def rename_attributes(self, old_name, new_name):
        renamed_count = 0
        for ng in bpy.data.node_groups:
            if ng.type == 'GEOMETRY':
                for node in ng.nodes:
                    if node.type == 'GROUP':
                        renamed_count += self.rename_attributes_in_group(node.node_tree, old_name, new_name)
                    else:
                        renamed_count += self.rename_attribute_node(node, old_name, new_name)
        return renamed_count

    def rename_attributes_in_group(self, node_tree, old_name, new_name):
        renamed_count = 0
        for node in node_tree.nodes:
            if node.type == 'GROUP':
                renamed_count += self.rename_attributes_in_group(node.node_tree, old_name, new_name)
            else:
                renamed_count += self.rename_attribute_node(node, old_name, new_name)
        return renamed_count

    def rename_attribute_node(self, node, old_name, new_name):
        renamed = 0
        
        attribute_nodes = {
            'GeometryNodeStoreNamedAttribute': 'Name',
            'GeometryNodeInputNamedAttribute': 'Name',
            'GeometryNodeRemoveAttribute': 'Name',
            'GeometryNodeCaptureAttribute': 'Name',
            'GeometryNodeAttributeStatistic': 'Attribute',
            'GeometryNodeAttributeDomainSize': 'Attribute'
        }
        
        if node.bl_idname in attribute_nodes:
            name_input = node.inputs.get(attribute_nodes[node.bl_idname])
            
            if name_input:
                if name_input.default_value == old_name:
                    name_input.default_value = new_name
                    renamed = 1
        return renamed

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

        box = layout.box()
        box.label(text="Rename")
        box.prop(scene, "old_attribute_name", text="Old Name")
        box.prop(scene, "new_attribute_name", text="New Name")
        box.operator("nodehelper.rename_attribute", text="Rename")

        box = layout.box()
        box.label(text="Find")
        box.prop(scene, "attribute_search_name", text="Search")
        box.operator("nodehelper.find_named_attributes", text="Find Attributes")

        box = layout.box()
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
            
            op = row.operator("nodehelper.jump_to_node", text=item.node_path, emboss=True)
            op.index = data.found_attributes.values().index(item)
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='NODE')

    def filter_items(self, context, data, propname):
        helpers = bpy.types.UI_UL_list
        items = getattr(data, propname)

        def parse_path(path):
            components = path.split(' > ')
            return tuple((comp, 'zzzz' if '(Group)' in comp else comp) for comp in components)

        sorted_items = sorted(enumerate(items), key=lambda x: parse_path(x[1].node_path))
        order = [i[0] for i in sorted_items]

        filter_flags = [self.bitflag_filter_item] * len(items)

        return filter_flags, order

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