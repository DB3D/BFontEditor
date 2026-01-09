import bpy

class BF_PT_MainPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "BFont Editor"
    bl_idname = "OBJECT_PT_bfont_editor"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BFont"

    def draw(self, context):
        layout = self.layout
        
        # File path display
        box = layout.box()
        box.label(text="Font File:")
        if hasattr(context.scene, 'bfont_filepath') and context.scene.bfont_filepath:
            # Display filepath (read-only)
            row = box.row()
            row.enabled = False
            row.prop(context.scene, "bfont_filepath", text="")
        else:
            box.label(text="No font loaded", icon='INFO')

        layout.separator()
        
        # Import/Export/Refresh
        box = layout.box()
        box.label(text="Import/Export:")
        box.operator("bfont.import_ttf", text="Import TTF", icon='IMPORT')
        box.operator("bfont.export_ttf", text="Export TTF", icon='EXPORT')
        box.operator("bfont.refresh_ttf", text="Refresh", icon='FILE_REFRESH')
        
        layout.separator()
        
        # Utilities
        box = layout.box()
        box.label(text="Utilities:")
        box.operator("bfont.group_to_center", text="Group to Center", icon='SNAP_FACE_CENTER')
        box.operator("bfont.group_orderly", text="Group Orderly", icon='GRID')
        
        layout.separator()
        
        # Text Display
        box = layout.box()
        box.label(text="Text Display:")
        box.operator("bfont.display_as_text", text="Display as Text", icon='FONT_DATA')
        box.operator("bfont.refresh_text_display", text="Refresh Text", icon='FILE_REFRESH')