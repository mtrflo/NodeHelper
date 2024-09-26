import bpy
from bpy.props import BoolProperty, StringProperty, FloatProperty, IntProperty, CollectionProperty
from bpy.types import PropertyGroup, Operator, Panel
from bpy.utils import register_class, unregister_class
from bpy.app.handlers import persistent

class CopiedInputProperty(PropertyGroup):
    name: StringProperty()
    value: StringProperty()

class CopiedInput(PropertyGroup):
    name: StringProperty()
    type: StringProperty()
    properties: CollectionProperty(type=CopiedInputProperty)

class NODEHELPER_OT_copy_selected_group_inputs(Operator):
    bl_idname = "nodehelper.copy_selected_group_inputs"
    bl_label = "Copy Selected Inputs"

    def execute(self, context):
        node = context.active_node
        if node.type != 'GROUP_INPUT':
            self.report({'ERROR'}, "Active node is not a Group Input node")
            return {'CANCELLED'}
        
        node_tree = node.id_data
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
                
                # Copy all available properties
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
                
                # Explicitly copy modifier and tool properties
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
        node = context.active_node
        if node.type != 'GROUP_INPUT':
            self.report({'ERROR'}, "Active node is not a Group Input node")
            return {'CANCELLED'}
        
        node_tree = node.id_data
        
        # Ensure the node group is editable
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
                
                # Set all properties
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
                
                # Set modifier and tool properties
                if is_modifier_prop:
                    is_modifier = is_modifier_prop.value.lower() == 'true'
                    if hasattr(node_tree, 'is_modifier'):
                        node_tree.is_modifier = is_modifier
                    else:
                        self.report({'WARNING'}, "Unable to set is_modifier: node_tree has no 'is_modifier' attribute")

                if is_tool_prop:
                    is_tool = is_tool_prop.value.lower() == 'true'
                    if hasattr(node_tree, 'is_tool'):
                        node_tree.is_tool = is_tool
                    else:
                        self.report({'WARNING'}, "Unable to set is_tool: node_tree has no 'is_tool' attribute")

                # After setting properties, update the node tree
                node_tree.update_tag()
                bpy.context.view_layer.update()

            except Exception as e:
                self.report({'ERROR'}, f"Failed to process socket {input_data.name}: {str(e)}")

        node_tree.update_tag()
        context.view_layer.update()
        
        self.report({'INFO'}, f"Updated {updated_count} existing inputs and created {created_count} new inputs")
        return {'FINISHED'}




def draw_group_io(self, context):
    print("draw_group_io function called")
    layout = self.layout
    node_tree = context.space_data.edit_tree

    if node_tree and node_tree.type == 'GEOMETRY':
        print(f"Node tree found: {node_tree.name}, type: {node_tree.type}")
        box = layout.box()
        box.label(text="Group IO")
        for socket in node_tree.interface.items_tree:
            if socket.item_type == 'SOCKET':
                print(f"Adding checkbox for socket: {socket.name}")
                row = box.row()
                row.prop(socket, "nodehelper_is_selected", text=socket.name)
        
        box.operator("nodehelper.copy_selected_group_inputs", text="Copy Selected")
        box.operator("nodehelper.paste_group_inputs", text="Paste")
    else:
        print("No suitable node tree found")

def register():
    print("Registering classes and properties")
    register_class(CopiedInputProperty)
    register_class(CopiedInput)
    register_class(NODEHELPER_OT_copy_selected_group_inputs)
    register_class(NODEHELPER_OT_paste_group_inputs)
    
    bpy.types.NodeTreeInterfaceSocket.nodehelper_is_selected = BoolProperty(default=False)
    bpy.types.Scene.copied_group_inputs = CollectionProperty(type=CopiedInput)

    print("Attempting to add draw function to NODE_PT_node_tree_interface")
    if hasattr(bpy.types, "NODE_PT_node_tree_interface"):
        print("NODE_PT_node_tree_interface found, appending draw function")
        bpy.types.NODE_PT_node_tree_interface.append(draw_group_io)
    else:
        print("NODE_PT_node_tree_interface not found")

    print("Registration complete")

def unregister():
    print("Unregistering addon")
    if hasattr(bpy.types, "NODE_PT_node_tree_interface"):
        print("Removing draw function from NODE_PT_node_tree_interface")
        bpy.types.NODE_PT_node_tree_interface.remove(draw_group_io)
    
    del bpy.types.Scene.copied_group_inputs
    del bpy.types.NodeTreeInterfaceSocket.nodehelper_is_selected
    
    unregister_class(NODEHELPER_OT_paste_group_inputs)
    unregister_class(NODEHELPER_OT_copy_selected_group_inputs)
    unregister_class(CopiedInput)
    unregister_class(CopiedInputProperty)
    print("Addon unregistered")

if __name__ == "__main__":
    print("Running register()")
    register()