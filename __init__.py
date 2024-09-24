bl_info = {
    "name": "Nodehelper",
    "author": "Fazoway",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "Node Editor > NodeHelper",
    "description": "This addon complements the tools for working with GeometryNodes.",
    "warning": "",
    "doc_url": "",
    "category": "Node",
}

import bpy
import os
import sys

# Add the Scripts directory to sys.path
addon_dir = os.path.dirname(__file__)
scripts_dir = os.path.join(addon_dir, "Scripts")
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

def import_submodule(module_name):
    import importlib
    return importlib.import_module(module_name)

def register():
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

if __name__ == "__main__":
    register()