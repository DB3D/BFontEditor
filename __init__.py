"""
BFontEditor
Import .ttf fonts as blender objects in the 3Dviewport
Edit them with blender builtin tools
Export them back as .ttf files
"""

import bpy
from bpy.props import StringProperty
from .ui import BF_PT_MainPanel
from .operators import (
    BF_OT_ImportFont, 
    BF_OT_ExportFont, 
    BF_OT_RefreshFont,
    BF_OT_GroupToCenter,
    BF_OT_GroupOrderly,
    BF_OT_DisplayAsText
)

bl_info = {
    "name": "BFont Editor",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > UI > BFont",
    "description": "Edit TTF fonts in Blender",
    "warning": "",
    "doc_url": "",
    "category": "Import-Export",
}

classes = (
    BF_OT_ImportFont,
    BF_OT_ExportFont,
    BF_OT_RefreshFont,
    BF_OT_GroupToCenter,
    BF_OT_GroupOrderly,
    BF_OT_DisplayAsText,
    BF_PT_MainPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register scene property for storing font filepath
    bpy.types.Scene.bfont_filepath = StringProperty(
        name="Font Path",
        description="Path to the TTF font file",
        default="",
        subtype='FILE_PATH'
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # Unregister scene property
    del bpy.types.Scene.bfont_filepath

if __name__ == "__main__":
    register()
