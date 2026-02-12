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
        
        # Active Character Info
        if context.active_object and context.active_object.type == 'CURVE':
            if context.active_object.get("glyph_name") and context.active_object.get("unicode"):
                box = layout.box()
                box.label(text="Active Character:", icon='FONT_DATA')
                
                # Display character in different formats using StringProperties
                row = box.row()
                row.enabled = False
                row.prop(context.scene, "bfont_char", text="Char")
                
                row = box.row()
                row.enabled = False
                row.prop(context.scene, "bfont_unicode", text="Unicode")
                
                row = box.row()
                row.enabled = False
                row.prop(context.scene, "bfont_decimal", text="Decimal")
                
                row = box.row()
                row.enabled = False
                row.prop(context.scene, "bfont_hex", text="Hex")
                
                row = box.row()
                row.enabled = False
                row.prop(context.scene, "bfont_glyph_name", text="Glyph")
                
                # Copy button
                box.operator("bfont.copy_char_info", text="Copy to Clipboard", icon='COPYDOWN')
                
                layout.separator()
        
        # File path display
        box = layout.box()
        box.label(text="Font File:")
        if hasattr(context.scene, 'bfont_filepath') and context.scene.bfont_filepath:
            row = box.row()
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
        box.operator("bfont.toggle_guides", text="Toggle Guides", icon='HIDE_OFF')
        
        layout.separator()
        
        # Mark Used/Unused
        box = layout.box()
        box.label(text="Mark Glyphs:")
        row = box.row(align=True)
        row.operator("bfont.set_used", text="Set Used", icon='CHECKMARK')
        row.operator("bfont.set_unused", text="Set Unused", icon='X')
        
        layout.separator()
        
        # Apply to Selection
        box = layout.box()
        box.label(text="Copy Glyph:")
        box.operator("bfont.apply_active_to_selected", text="Apply Active to Selected", icon='DUPLICATE')
        box.operator("bfont.merge_into_selected", text="Merge Into Selected", icon='MOD_BOOLEAN')
        box.operator("bfont.fix_glyph_data", text="Fix All Glyph Data", icon='FILE_REFRESH')
        
        layout.separator()
        
        # Text Display
        box = layout.box()
        box.label(text="Text Display:")
        box.operator("bfont.display_as_text", text="Display as Text", icon='FONT_DATA')
        box.operator("bfont.refresh_text_display", text="Refresh Text", icon='FILE_REFRESH')