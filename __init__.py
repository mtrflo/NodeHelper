bl_info = {
    "name": "Node Helper",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "Node Editor > Sidebar > NodeHelper",
    "description": "Adds functionality to help with node management",
    "warning": "",
    "doc_url": "",
    "category": "Node",
}

import bpy
from . import attribute,group_input,copy_groupInputs
from . import frame

modules = [
    attribute,
    group_input,
    copy_groupInputs
]

def register():
    for module in modules:
        module.register()
    frame.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
    frame.unregister()

if __name__ == "__main__":
    register()