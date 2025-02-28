bl_info = {
    "name": "NodeHelper",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "Node Editor > Sidebar > NodeHelper",
    "description": "Helpful tools for working with nodes",
    "category": "Node",
}

import bpy
from . import group_input
from . import frame
from . import attribute
from . import node_utils

def register():
    group_input.register()
    frame.register()
    attribute.register()
    node_utils.register()

def unregister():
    attribute.unregister()
    frame.unregister()
    group_input.unregister()
    node_utils.unregister()

if __name__ == "__main__":
    register()