bl_info = {
    "name": "Nodehelper",
    "author": "Fazoway",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "Node Editor > NodeHelper",
    "description": "This addon complements the tools for working with GeometryNodes.",
    "warning": "",
    "doc_url": "",  # You can add a documentation URL if you have one
    "category": "Node",
}

import bpy
import os
import sys
from bpy.props import StringProperty, CollectionProperty
from bpy.types import Panel, PropertyGroup

# Add the Scripts directory to sys.path
addon_dir = os.path.dirname(__file__)
scripts_dir = os.path.join(addon_dir, "Scripts")
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

class FoundAttribute(PropertyGroup):
    node_path: StringProperty()

class NODEHELPER_PT_named_attributes(Panel):
    bl_label = "NamedAttribute"
    bl_idname = "NODEHELPER_PT_named_attributes"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "NodeHelper"
    bl_order = 1
    
    @classmethod
    def poll(cls, context):
        return (context.space_data.type == 'NODE_EDITOR' and
                context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "attribute_search_name", text="Search Name")
        layout.operator("nodehelper.find_named_attributes", text="Find Attributes")

        if hasattr(scene, "found_attributes"):
            for i, item in enumerate(scene.found_attributes):
                box = layout.box()
                row = box.row()
                row.label(text=f"{item.node_path}")
                row.operator("nodehelper.jump_to_node", text="", icon='VIEWZOOM').index = i

        layout.separator()
        layout.label(text="Rename Attribute")
        col = layout.column(align=True)
        col.prop(scene, "old_attribute_name", text="Old Name")
        col.prop(scene, "new_attribute_name", text="New Name")
        layout.operator("nodehelper.rename_attribute", text="Rename")

def import_submodule(module_name):
    import importlib
    return importlib.import_module(module_name)

def register():
    bpy.utils.register_class(FoundAttribute)
    bpy.utils.register_class(NODEHELPER_PT_named_attributes)
    
    bpy.types.Scene.attribute_search_name = StringProperty(
        name="Search Name",
        description="Enter the name to search for",
        default=""
    )
    
    bpy.types.Scene.old_attribute_name = StringProperty(
        name="Old Attribute Name",
        description="Enter the old attribute name",
        default=""
    )
    
    bpy.types.Scene.new_attribute_name = StringProperty(
        name="New Attribute Name",
        description="Enter the new attribute name",
        default=""
    )
    
    bpy.types.Scene.found_attributes = CollectionProperty(type=FoundAttribute)
    
    # Import and register submodules
    for module_name in ['general', 'input_navigator', 'groupIO', 'rename', 'find']:
        try:
            module = import_submodule(module_name)
            if hasattr(module, 'register'):
                module.register()
        except ImportError as e:
            print(f"Error importing {module_name}: {e}")

def unregister():
    # Import and unregister submodules
    for module_name in ['find', 'rename', 'groupIO', 'input_navigator', 'general']:
        try:
            module = import_submodule(module_name)
            if hasattr(module, 'unregister'):
                module.unregister()
        except ImportError as e:
            print(f"Error importing {module_name}: {e}")
    
    del bpy.types.Scene.found_attributes
    del bpy.types.Scene.new_attribute_name
    del bpy.types.Scene.old_attribute_name
    del bpy.types.Scene.attribute_search_name
    
    bpy.utils.unregister_class(NODEHELPER_PT_named_attributes)
    bpy.utils.unregister_class(FoundAttribute)

if __name__ == "__main__":
    register()
    