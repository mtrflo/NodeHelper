import bpy
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, IntProperty, BoolProperty, CollectionProperty

# Property Groups for Copy/Paste functionality
class CopiedInputProperty(PropertyGroup):
    name: StringProperty()
    value: StringProperty()

class CopiedInput(PropertyGroup):
    name: StringProperty()
    type: StringProperty()
    properties: CollectionProperty(type=CopiedInputProperty)

# Operators for Group Input Management
class NODEHELPER_OT_hide_unused_sockets(Operator):
    bl_idname = "nodehelper.hide_unused_sockets"
    bl_label = "Hide Group Input Unused Sockets"
    bl_description = "Hide all unused sockets in the Group Input node"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        space = context.space_data
        active_tree = space.edit_tree or space.node_tree
        
        if active_tree:
            for node in active_tree.nodes:
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
        space = context.space_data
        active_tree = space.edit_tree or space.node_tree
        if not active_tree:
            return {'CANCELLED'}

        mouse_x, mouse_y = context.region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
        input_node = active_tree.nodes.new(type='NodeGroupInput')
        input_node.location = mouse_x, mouse_y

        if active_tree.type == 'GROUP':
            existing_input = active_tree.inputs.get(self.input_name)
            if not existing_input:
                new_input = active_tree.inputs.new('NodeSocketGeometry', self.input_name)
            else:
                new_input = existing_input

            for output in input_node.outputs:
                if output.name == new_input.name:
                    output.hide = False
                else:
                    output.hide = True
        else:
            for output in input_node.outputs:
                if output.name == self.input_name:
                    output.hide = False
                else:
                    output.hide = True

        for node in active_tree.nodes:
            node.select = False
        input_node.select = True
        active_tree.nodes.active = input_node

        bpy.ops.transform.translate('INVOKE_DEFAULT')
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
                        break
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

        current_index = context.scene.nodehelper_current_node_index
        next_index = (current_index + 1) % len(connected_nodes)
        context.scene.nodehelper_current_node_index = next_index

        for node in active_tree.nodes:
            node.select = False
        
        connected_node = connected_nodes[next_index]
        connected_node.select = True
        active_tree.nodes.active = connected_node

        bpy.ops.node.view_selected()

        self.report({'INFO'}, f"Jumped to node {next_index + 1}/{len(connected_nodes)} using input: {self.input_name}")
        return {'FINISHED'}

# Copy/Paste Operators
class NODEHELPER_OT_copy_selected_group_inputs(Operator):
    bl_idname = "nodehelper.copy_selected_group_inputs"
    bl_label = "Copy Selected Inputs"

    def execute(self, context):
        node_tree = context.space_data.edit_tree
        if not node_tree or node_tree.type != 'GEOMETRY':
            self.report({'ERROR'}, "No active Geometry Node group")
            return {'CANCELLED'}
        
        node_tree.update_tag()
        context.view_layer.update()
        
        context.scene.copied_group_inputs.clear()
        
        copied_count = 0
        for input in node_tree.interface.items_tree:
            if input.item_type == 'SOCKET' and getattr(input, "nodehelper_is_selected", False):
                item = context.scene.copied_group_inputs.add()
                item.name = input.name
                item.type = input.bl_socket_idname
                
                item.properties.clear()
                
                for prop in input.bl_rna.properties:
                    if not prop.is_readonly:
                        try:
                            value = getattr(input, prop.identifier)
                            prop_item = item.properties.add()
                            prop_item.name = prop.identifier
                            if isinstance(value, (bool, int, float, str)):
                                prop_item.value = str(value)
                            elif isinstance(value, (tuple, list)):
                                prop_item.value = ','.join(map(str, value))
                        except Exception as e:
                            self.report({'WARNING'}, f"Failed to copy property {prop.identifier}: {str(e)}")
                
                prop_item = item.properties.add()
                prop_item.name = 'is_modifier'
                prop_item.value = str(node_tree.is_modifier)

                prop_item = item.properties.add()
                prop_item.name = 'is_tool'
                prop_item.value = str(node_tree.is_tool)
                
                copied_count += 1
        
        self.report({'INFO'}, f"Copied {copied_count} selected inputs")
        return {'FINISHED'}

class NODEHELPER_OT_paste_group_inputs(Operator):
    bl_idname = "nodehelper.paste_group_inputs"
    bl_label = "Paste Inputs"

    def execute(self, context):
        node_tree = context.space_data.edit_tree
        if not node_tree or node_tree.type != 'GEOMETRY':
            self.report({'ERROR'}, "No active Geometry Node group")
            return {'CANCELLED'}
        
        if node_tree.library or node_tree.override_library:
            try:
                bpy.ops.node.group_make_local()
            except Exception as e:
                self.report({'ERROR'}, f"Failed to make node group editable: {str(e)}")
                return {'CANCELLED'}
        
        if not node_tree.is_embedded_data:
            node_tree.use_fake_user = True

        updated_count = 0
        created_count = 0
        for input_data in context.scene.copied_group_inputs:
            existing_socket = next((s for s in node_tree.interface.items_tree if s.name == input_data.name), None)
            
            is_modifier_prop = next((p for p in input_data.properties if p.name == 'is_modifier'), None)
            is_tool_prop = next((p for p in input_data.properties if p.name == 'is_tool'), None)
            
            try:
                if existing_socket:
                    socket = existing_socket
                    updated_count += 1
                else:
                    socket = node_tree.interface.new_socket(
                        name=input_data.name,
                        in_out='INPUT',
                        socket_type=input_data.type
                    )
                    created_count += 1
                
                for prop in input_data.properties:
                    if hasattr(socket, prop.name) and prop.name not in ['is_modifier', 'is_tool']:
                        try:
                            value = getattr(socket, prop.name)
                            if isinstance(value, bool):
                                setattr(socket, prop.name, prop.value.lower() == 'true')
                            elif isinstance(value, int):
                                setattr(socket, prop.name, int(float(prop.value)))
                            elif isinstance(value, float):
                                setattr(socket, prop.name, float(prop.value))
                            elif isinstance(value, (tuple, list)):
                                setattr(socket, prop.name, tuple(map(float, prop.value.split(','))))
                            else:
                                setattr(socket, prop.name, prop.value)
                        except Exception as e:
                            self.report({'WARNING'}, f"Failed to set property {prop.name}: {str(e)}")
                
                if is_modifier_prop and hasattr(node_tree, 'is_modifier'):
                    node_tree.is_modifier = is_modifier_prop.value.lower() == 'true'

                if is_tool_prop and hasattr(node_tree, 'is_tool'):
                    node_tree.is_tool = is_tool_prop.value.lower() == 'true'

            except Exception as e:
                self.report({'ERROR'}, f"Failed to process socket {input_data.name}: {str(e)}")

        node_tree.update_tag()
        context.view_layer.update()
        
        self.report({'INFO'}, f"Updated {updated_count} existing inputs and created {created_count} new inputs")
        return {'FINISHED'}

# Panel Classes
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
        space = context.space_data

        if space.edit_tree and space.edit_tree != space.node_tree:
            tree = space.edit_tree
        else:
            tree = space.node_tree

        # Group Input Operations
        box = layout.box()
        box.label(text="Group Input Operations")
        
        row = box.row()
        row.scale_y = 1.5
        row.operator("nodehelper.hide_unused_sockets", text="Hide Unused Sockets")

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
                    if not output.name:
                        continue
                    
                    if search_term in output.name.lower():
                        row = col.row(align=True)
                        row.scale_y = 1.5
                        
                        split = row.split(factor=0.8)
                        op = split.operator("nodehelper.drag_input", text=output.name)
                        op.input_name = output.name
                        
                        op = split.operator("nodehelper.jump_to_connected_node", text="", icon='VIEWZOOM')
                        op.input_name = output.name
                        
                        col.separator(factor=0.2)

        # Copy & Paste Interface
        if tree and tree.type == 'GEOMETRY':
            box = layout.box()
            box.label(text="Copy & Paste")
            
            for socket in tree.interface.items_tree:
                if socket.item_type == 'SOCKET':
                    row = box.row()
                    row.prop(socket, "nodehelper_is_selected", text=socket.name)
            
            row = box.row(align=True)
            row.operator("nodehelper.copy_selected_group_inputs", text="Copy Selected")
            row.operator("nodehelper.paste_group_inputs", text="Paste")

def register():
    bpy.utils.register_class(CopiedInputProperty)
    bpy.utils.register_class(CopiedInput)
    bpy.utils.register_class(NODEHELPER_OT_hide_unused_sockets)
    bpy.utils.register_class(NODEHELPER_OT_jump_to_connected_node)
    bpy.utils.register_class(NODEHELPER_OT_drag_input)
    bpy.utils.register_class(NODEHELPER_OT_copy_selected_group_inputs)
    bpy.utils.register_class(NODEHELPER_OT_paste_group_inputs)
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
    bpy.types.NodeTreeInterfaceSocket.nodehelper_is_selected = BoolProperty(default=False)
    bpy.types.Scene.copied_group_inputs = CollectionProperty(type=CopiedInput)

def unregister():
    bpy.utils.unregister_class(NODEHELPER_PT_group_input)
    bpy.utils.unregister_class(NODEHELPER_OT_paste_group_inputs)
    bpy.utils.unregister_class(NODEHELPER_OT_copy_selected_group_inputs)
    bpy.utils.unregister_class(NODEHELPER_OT_drag_input)
    bpy.utils.unregister_class(NODEHELPER_OT_jump_to_connected_node)
    bpy.utils.unregister_class(NODEHELPER_OT_hide_unused_sockets)
    bpy.utils.unregister_class(CopiedInput)
    bpy.utils.unregister_class(CopiedInputProperty)
    
    del bpy.types.Scene.nodehelper_input_search
    del bpy.types.Scene.nodehelper_current_node_index
    del bpy.types.NodeTreeInterfaceSocket.nodehelper_is_selected
    del bpy.types.Scene.copied_group_inputs

if __name__ == "__main__":
    register()