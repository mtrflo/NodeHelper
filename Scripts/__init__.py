import bpy
from bpy.props import StringProperty, CollectionProperty
from bpy.types import Panel, PropertyGroup
from . import input_navigator
from . import groupIO

class FoundAttribute(PropertyGroup):
    node_path: StringProperty()

class NODEHELPER_PT_named_attributes(Panel):
    bl_label = "NamedAttribute"
    bl_idname = "NODEHELPER_PT_named_attributes"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "NodeHelper"

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

def register():
    bpy.utils.register_class(FoundAttribute)
    
    from . import general
    general.register()  # Register General panel first
    
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
    
    from . import rename, find
    rename.register()
    find.register()
    input_navigator.register()
    groupIO.register()  # Add this line

def unregister():
    from . import rename, find, general
    find.unregister()
    rename.unregister()
    
    del bpy.types.Scene.found_attributes
    del bpy.types.Scene.new_attribute_name
    del bpy.types.Scene.old_attribute_name
    del bpy.types.Scene.attribute_search_name
    
    bpy.utils.unregister_class(NODEHELPER_PT_named_attributes)
    bpy.utils.unregister_class(FoundAttribute)
    
    general.unregister()  # Unregister General panel last
    input_navigator.unregister()
    groupIO.unregister()  # Add this line

if __name__ == "__main__":
    register()  