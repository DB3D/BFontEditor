import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.types import Operator
from .font_utils import import_ttf_file, export_ttf_file

class BF_OT_ImportFont(Operator, ImportHelper):
    """Import a .ttf font file as editable curves"""
    bl_idname = "bfont.import_ttf"
    bl_label = "Import TTF"
    
    filter_glob: bpy.props.StringProperty(
        default="*.ttf;*.otf",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        return import_ttf_file(self.filepath, context)


class BF_OT_ExportFont(Operator):
    """Export the current object (and siblings) back to the TTF file"""
    bl_idname = "bfont.export_ttf"
    bl_label = "Export TTF"

    def execute(self, context):
        # Use stored filepath
        filepath = context.scene.bfont_filepath if hasattr(context.scene, 'bfont_filepath') else ""
        if not filepath:
            self.report({'ERROR'}, "No font file loaded. Import a font first.")
            return {'CANCELLED'}
        return export_ttf_file(filepath, context)


class BF_OT_RefreshFont(Operator):
    """Reload the font from the stored filepath"""
    bl_idname = "bfont.refresh_ttf"
    bl_label = "Refresh Font"
    
    def execute(self, context):
        filepath = context.scene.bfont_filepath if hasattr(context.scene, 'bfont_filepath') else ""
        if not filepath:
            self.report({'ERROR'}, "No font file loaded. Import a font first.")
            return {'CANCELLED'}
        
        # Clear existing collections with font data
        # (Implementation could be more sophisticated)
        self.report({'INFO'}, f"Reloading from {filepath}")
        return import_ttf_file(filepath, context)


class BF_OT_GroupToCenter(Operator):
    """Move all selected glyphs to origin"""
    bl_idname = "bfont.group_to_center"
    bl_label = "Group to Center"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        for obj in context.selected_objects:
            if obj.get("glyph_name"):
                obj.location = (0, 0, 0)
        return {'FINISHED'}


class BF_OT_GroupOrderly(Operator):
    """Arrange glyphs in a grid mosaic"""
    bl_idname = "bfont.group_orderly"
    bl_label = "Group Orderly"
    bl_options = {'REGISTER', 'UNDO'}
    
    items_per_row: bpy.props.IntProperty(
        name="Items per Row",
        default=20,
        min=1,
        max=100
    )
    
    spacing: bpy.props.FloatProperty(
        name="Spacing",
        default=1.5,
        min=0.1,
        max=10.0
    )
    
    def execute(self, context):
        # Get all glyph objects
        glyphs = [obj for obj in context.selected_objects if obj.get("glyph_name")]
        
        # Sort by unicode if available, otherwise by name
        glyphs.sort(key=lambda obj: obj.get("unicode", 999999))
        
        # Arrange in grid
        for i, obj in enumerate(glyphs):
            row = i // self.items_per_row
            col = i % self.items_per_row
            
            obj.location.x = col * self.spacing
            obj.location.y = -row * self.spacing
            obj.location.z = 0
        
        self.report({'INFO'}, f"Arranged {len(glyphs)} glyphs in grid")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class BF_OT_DisplayAsText(Operator):
    """Display the font as text"""
    bl_idname = "bfont.display_as_text"
    bl_label = "Display as Text"
    bl_options = {'REGISTER', 'UNDO'}
    
    text_content: bpy.props.StringProperty(
        name="Text",
        default="AaBbCc 123",
        maxlen=1024
    )
    
    spacing: bpy.props.FloatProperty(
        name="Spacing",
        default=1.2,
        min=0.1,
        max=10.0
    )
    
    def execute(self, context):
        # Get all glyph objects in the scene
        glyph_map = {}
        for obj in context.scene.objects:
            if obj.get("glyph_name"):
                unicode_val = obj.get("unicode")
                if unicode_val:
                    glyph_map[chr(unicode_val)] = obj
        
        if not glyph_map:
            self.report({'ERROR'}, "No font glyphs found. Import a font first.")
            return {'CANCELLED'}
        
        # Position each character
        x_offset = 0
        for char in self.text_content:
            if char in glyph_map:
                obj = glyph_map[char]
                obj.location.x = x_offset
                obj.location.y = 0
                obj.location.z = 0
                x_offset += self.spacing
            elif char == ' ':
                x_offset += self.spacing * 0.5
        
        self.report({'INFO'}, f"Displayed text: {self.text_content}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
