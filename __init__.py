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
    BF_OT_DisplayAsText,
    BF_OT_RefreshTextDisplay,
    BF_OT_ToggleGuides,
    BF_OT_SetUsed,
    BF_OT_SetUnused,
    BF_OT_CopyCharInfo
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
    BF_OT_RefreshTextDisplay,
    BF_OT_ToggleGuides,
    BF_OT_SetUsed,
    BF_OT_SetUnused,
    BF_OT_CopyCharInfo,
    BF_PT_MainPanel,
)

# Getter functions for dynamic properties
def get_active_char(self):
    if bpy.context.active_object and bpy.context.active_object.type == 'CURVE':
        if bpy.context.active_object.get("unicode"):
            return chr(bpy.context.active_object.get("unicode"))
    return ""

def get_active_unicode(self):
    if bpy.context.active_object and bpy.context.active_object.type == 'CURVE':
        if bpy.context.active_object.get("unicode"):
            unicode_val = bpy.context.active_object.get("unicode")
            return f"U+{unicode_val:04X}"
    return ""

def get_active_decimal(self):
    if bpy.context.active_object and bpy.context.active_object.type == 'CURVE':
        if bpy.context.active_object.get("unicode"):
            return str(bpy.context.active_object.get("unicode"))
    return ""

def get_active_hex(self):
    if bpy.context.active_object and bpy.context.active_object.type == 'CURVE':
        if bpy.context.active_object.get("unicode"):
            unicode_val = bpy.context.active_object.get("unicode")
            return f"0x{unicode_val:02X}"
    return ""

def get_active_glyph_name(self):
    if bpy.context.active_object and bpy.context.active_object.type == 'CURVE':
        if bpy.context.active_object.get("glyph_name"):
            return bpy.context.active_object.get("glyph_name")
    return ""

def set_dummy(self, value):
    """Dummy setter to make properties read-only"""
    pass

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
    
    # Register character info properties with getters
    bpy.types.Scene.bfont_char = StringProperty(
        name="Char",
        description="Active character",
        get=get_active_char,
        set=set_dummy
    )
    bpy.types.Scene.bfont_unicode = StringProperty(
        name="Unicode",
        description="Unicode value",
        get=get_active_unicode,
        set=set_dummy
    )
    bpy.types.Scene.bfont_decimal = StringProperty(
        name="Decimal",
        description="Decimal value",
        get=get_active_decimal,
        set=set_dummy
    )
    bpy.types.Scene.bfont_hex = StringProperty(
        name="Hex",
        description="Hexadecimal value",
        get=get_active_hex,
        set=set_dummy
    )
    bpy.types.Scene.bfont_glyph_name = StringProperty(
        name="Glyph",
        description="Glyph name",
        get=get_active_glyph_name,
        set=set_dummy
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # Unregister scene properties
    del bpy.types.Scene.bfont_filepath
    del bpy.types.Scene.bfont_char
    del bpy.types.Scene.bfont_unicode
    del bpy.types.Scene.bfont_decimal
    del bpy.types.Scene.bfont_hex
    del bpy.types.Scene.bfont_glyph_name

if __name__ == "__main__":
    register()
