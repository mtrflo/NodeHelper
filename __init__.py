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
from . import attribute
from . import general
from . import input_navigator
from . import groupIO

modules = [
    attribute,
    general,
    input_navigator,
    groupIO
]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()

if __name__ == "__main__":
    register()