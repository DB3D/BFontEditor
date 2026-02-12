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
    """Move all guide meshes (parents) to origin"""
    bl_idname = "bfont.group_to_center"
    bl_label = "Group to Center"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Find all guide meshes (parents of glyphs) - no selection needed
        guide_meshes = []
        for obj in context.scene.objects:
            # Look for objects with children that have glyph_name
            if obj.children:
                for child in obj.children:
                    if child.get("glyph_name"):
                        guide_meshes.append(obj)
                        break
        
        # Move all guide meshes to origin
        for guide in guide_meshes:
            guide.location = (0, 0, 0)
        
        self.report({'INFO'}, f"Centered {len(guide_meshes)} glyphs")
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
        # Find all guide meshes (parents) with their glyph children - no selection needed
        guide_data = []
        for obj in context.scene.objects:
            if obj.children:
                for child in obj.children:
                    if child.get("glyph_name"):
                        unicode_val = child.get("unicode", 999999)
                        guide_data.append((obj, unicode_val))
                        break
        
        # Sort by unicode
        guide_data.sort(key=lambda x: x[1])
        
        # Arrange guide meshes in grid
        for i, (guide, _) in enumerate(guide_data):
            row = i // self.items_per_row
            col = i % self.items_per_row
            
            guide.location.x = col * self.spacing
            guide.location.y = -row * self.spacing
            guide.location.z = 0
        
        self.report({'INFO'}, f"Arranged {len(guide_data)} glyphs in grid")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class BF_OT_DisplayAsText(Operator):
    """Display the font as a Blender text object"""
    bl_idname = "bfont.display_as_text"
    bl_label = "Display as Text"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Get the stored font filepath
        filepath = context.scene.bfont_filepath if hasattr(context.scene, 'bfont_filepath') else ""
        if not filepath:
            self.report({'ERROR'}, "No font file loaded. Import a font first.")
            return {'CANCELLED'}
        
        # Load the font into Blender
        try:
            font_data = bpy.data.fonts.load(filepath)
        except:
            self.report({'ERROR'}, f"Could not load font from {filepath}")
            return {'CANCELLED'}
        
        # Create text curve object
        text_curve = bpy.data.curves.new(name="FontDisplay", type='FONT')
        text_curve.font = font_data
        
        # Get all available characters with unicode values
        char_list = []
        for obj in context.scene.objects:
            if obj.get("glyph_name") and obj.get("unicode"):
                unicode_val = obj.get("unicode")
                char_list.append((unicode_val, chr(unicode_val)))
        
        # Sort by unicode value
        char_list.sort(key=lambda x: x[0])
        
        # Build text string with all characters
        text_content = ''.join([char for _, char in char_list])
        text_curve.body = text_content
        
        # Set text properties
        text_curve.size = 1.0
        text_curve.space_character = 1.2
        
        # Create object
        text_obj = bpy.data.objects.new("FontDisplay", text_curve)
        context.collection.objects.link(text_obj)
        text_obj.location = (0, 0, 0)
        
        self.report({'INFO'}, f"Created text display with {len(char_list)} characters")
        return {'FINISHED'}


class BF_OT_RefreshTextDisplay(Operator):
    """Refresh the text display object with updated font"""
    bl_idname = "bfont.refresh_text_display"
    bl_label = "Refresh Text Display"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Find existing FontDisplay object
        text_obj = None
        for obj in context.scene.objects:
            if obj.type == 'FONT' and obj.name.startswith("FontDisplay"):
                text_obj = obj
                break
        
        if not text_obj:
            self.report({'WARNING'}, "No text display found. Creating new one.")
            return bpy.ops.bfont.display_as_text()
        
        # Get the stored font filepath
        filepath = context.scene.bfont_filepath if hasattr(context.scene, 'bfont_filepath') else ""
        if not filepath:
            self.report({'ERROR'}, "No font file loaded.")
            return {'CANCELLED'}
        
        # Reload the font
        try:
            font_data = bpy.data.fonts.load(filepath)
            text_obj.data.font = font_data
        except:
            self.report({'ERROR'}, f"Could not reload font from {filepath}")
            return {'CANCELLED'}
        
        # Update character list
        char_list = []
        for obj in context.scene.objects:
            if obj.get("glyph_name") and obj.get("unicode"):
                unicode_val = obj.get("unicode")
                char_list.append((unicode_val, chr(unicode_val)))
        
        char_list.sort(key=lambda x: x[0])
        text_content = ''.join([char for _, char in char_list])
        text_obj.data.body = text_content
        
        self.report({'INFO'}, f"Refreshed text display with {len(char_list)} characters")
        return {'FINISHED'}


class BF_OT_ToggleGuides(Operator):
    """Toggle visibility of all guide meshes"""
    bl_idname = "bfont.toggle_guides"
    bl_label = "Toggle Guides"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Find all guide meshes (parents of glyphs)
        guide_meshes = []
        for obj in context.scene.objects:
            # Look for objects with children that have glyph_name
            if obj.children:
                for child in obj.children:
                    if child.get("glyph_name"):
                        guide_meshes.append(obj)
                        break
        
        if not guide_meshes:
            self.report({'WARNING'}, "No guide meshes found")
            return {'CANCELLED'}
        
        # Determine current state (if any guide is visible, we hide all; if all hidden, we show all)
        any_visible = any(not g.hide_viewport for g in guide_meshes)
        
        # Toggle visibility
        for guide in guide_meshes:
            guide.hide_viewport = any_visible
            guide.hide_render = True  # Always hide from render
        
        state = "hidden" if any_visible else "visible"
        self.report({'INFO'}, f"Guides {state} ({len(guide_meshes)} objects)")
        return {'FINISHED'}


class BF_OT_SetUsed(Operator):
    """Mark selected glyphs as used (white color)"""
    bl_idname = "bfont.set_used"
    bl_label = "Set Used"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if not context.selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        
        count = 0
        for obj in context.selected_objects:
            # If this is a curve object directly, color it
            if obj.type == 'CURVE' and obj.get("glyph_name"):
                obj.color = (1.0, 1.0, 1.0, 1.0)  # White
                count += 1
            # Otherwise check if this is a guide parent
            else:
                for child in obj.children:
                    if child.type == 'CURVE' and child.get("glyph_name"):
                        # Found the curve character object
                        child.color = (1.0, 1.0, 1.0, 1.0)  # White
                        count += 1
                        break
        
        self.report({'INFO'}, f"Marked {count} glyphs as used")
        return {'FINISHED'}


class BF_OT_SetUnused(Operator):
    """Mark selected glyphs as unused (dark gray color)"""
    bl_idname = "bfont.set_unused"
    bl_label = "Set Unused"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if not context.selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        
        count = 0
        for obj in context.selected_objects:
            # If this is a curve object directly, color it
            if obj.type == 'CURVE' and obj.get("glyph_name"):
                obj.color = (0.087282, 0.087282, 0.087282, 1.0)  # Dark gray
                count += 1
            # Otherwise check if this is a guide parent
            else:
                for child in obj.children:
                    if child.type == 'CURVE' and child.get("glyph_name"):
                        # Found the curve character object
                        child.color = (0.087282, 0.087282, 0.087282, 1.0)  # Dark gray
                        count += 1
                        break
        
        self.report({'INFO'}, f"Marked {count} glyphs as unused")
        return {'FINISHED'}


class BF_OT_CopyCharInfo(Operator):
    """Copy active character information to clipboard"""
    bl_idname = "bfont.copy_char_info"
    bl_label = "Copy Character Info"
    bl_options = {'REGISTER'}
    
    format_type: bpy.props.EnumProperty(
        name="Format",
        description="Format to copy",
        items=[
            ('CHAR', "Character", "Copy the character itself"),
            ('UNICODE', "Unicode", "Copy Unicode format (U+XXXX)"),
            ('DECIMAL', "Decimal", "Copy decimal value"),
            ('HEX', "Hexadecimal", "Copy hex value (0xXX)"),
            ('HTML', "HTML Entity", "Copy HTML entity (&#XXXX;)"),
            ('ALL', "All Formats", "Copy all formats as text"),
        ],
        default='ALL'
    )
    
    def execute(self, context):
        if not context.active_object or context.active_object.type != 'CURVE':
            self.report({'WARNING'}, "No curve object selected")
            return {'CANCELLED'}
        
        if not context.active_object.get("glyph_name") or not context.active_object.get("unicode"):
            self.report({'WARNING'}, "Selected object is not a font glyph")
            return {'CANCELLED'}
        
        unicode_val = context.active_object.get("unicode")
        char = chr(unicode_val)
        glyph_name = context.active_object.get("glyph_name")
        
        # Build the text to copy based on format
        if self.format_type == 'CHAR':
            text = char
        elif self.format_type == 'UNICODE':
            text = f"U+{unicode_val:04X}"
        elif self.format_type == 'DECIMAL':
            text = str(unicode_val)
        elif self.format_type == 'HEX':
            text = f"0x{unicode_val:02X}"
        elif self.format_type == 'HTML':
            text = f"&#{unicode_val};"
        else:  # ALL
            text = f"""Character: {char}
Unicode: U+{unicode_val:04X}
Decimal: {unicode_val}
Hex: 0x{unicode_val:02X}
HTML: &#{unicode_val};
Glyph Name: {glyph_name}"""
        
        # Copy to clipboard (Windows)
        context.window_manager.clipboard = text
        
        self.report({'INFO'}, f"Copied to clipboard: {self.format_type}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class BF_OT_ApplyActiveToSelected(Operator):
    """Copy all curves/meshes/text from active guide to selected guides"""
    bl_idname = "bfont.apply_active_to_selected"
    bl_label = "Apply Active to Selected"
    bl_options = {'REGISTER', 'UNDO'}
    
    keep_existing: bpy.props.BoolProperty(
        name="Keep Existing",
        description="Keep existing children on target guides",
        default=False
    )
    
    def execute(self, context):
        active = context.active_object
        
        # Check if active is a guide parent (has glyph children)
        if not active:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}
        
        # Build a lookup table from glyph_name to unicode from ALL scene data FIRST
        unicode_lookup = {}
        for obj in context.scene.objects:
            if obj.get("glyph_name") and obj.get("unicode"):
                unicode_lookup[obj.get("glyph_name")] = obj.get("unicode")
        
        # Find source children (from active guide)
        source_children = []
        active_is_guide = False
        
        for child in active.children:
            if child.get("glyph_name") or child.type in ('CURVE', 'MESH', 'FONT'):
                source_children.append(child)
                active_is_guide = True
        
        if not active_is_guide:
            self.report({'ERROR'}, "Active object is not a guide parent (no valid children)")
            return {'CANCELLED'}
        
        if not source_children:
            self.report({'ERROR'}, "Active guide has no children to copy")
            return {'CANCELLED'}
        
        # Find target guides (selected, excluding active)
        target_guides = []
        for obj in context.selected_objects:
            if obj == active:
                continue
            # Check if it's a guide (has children with glyph_name or is a guide mesh)
            is_guide = False
            for child in obj.children:
                if child.get("glyph_name"):
                    is_guide = True
                    break
            # Also check if it's named as a guide
            if "_Guide" in obj.name:
                is_guide = True
            if is_guide:
                target_guides.append(obj)
        
        if not target_guides:
            self.report({'ERROR'}, "No target guides selected")
            return {'CANCELLED'}
        
        copied_count = 0
        
        for target_guide in target_guides:
            # Extract glyph_name from guide name (handle .001 suffix)
            target_glyph_name = target_guide.name.replace("_Guide", "").split(".")[0]
            
            # Get unicode from lookup table
            target_unicode = unicode_lookup.get(target_glyph_name)
            
            # Optionally remove existing children
            if not self.keep_existing:
                for child in list(target_guide.children):
                    if child.type in ('CURVE', 'MESH', 'FONT'):
                        bpy.data.objects.remove(child, do_unlink=True)
            
            # Copy each source child to target
            for source in source_children:
                # Duplicate object and data
                new_obj = source.copy()
                new_obj.data = source.data.copy()
                
                # Link to scene
                context.collection.objects.link(new_obj)
                
                # Parent to target guide
                new_obj.parent = target_guide
                new_obj.matrix_parent_inverse = target_guide.matrix_world.inverted()
                
                # Copy the local transform from source
                new_obj.matrix_local = source.matrix_local.copy()
                
                # Update glyph_name to match target
                new_obj["glyph_name"] = target_glyph_name
                
                # Set unicode from lookup
                if target_unicode:
                    new_obj["unicode"] = target_unicode
                
                copied_count += 1
        
        self.report({'INFO'}, f"Copied {len(source_children)} objects to {len(target_guides)} guides ({copied_count} total)")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class BF_OT_FixGlyphData(Operator):
    """Fix/restore glyph_name and unicode on ALL guides' children in scene"""
    bl_idname = "bfont.fix_glyph_data"
    bl_label = "Fix All Glyph Data"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Load the TTF to get the authoritative cmap (glyph_name -> unicode)
        filepath = context.scene.bfont_filepath if hasattr(context.scene, 'bfont_filepath') else ""
        
        # Build glyph_name -> unicode lookup from the TTF file
        unicode_lookup = {}
        if filepath:
            try:
                from fontTools.ttLib import TTFont
                font = TTFont(filepath)
                cmap = font.getBestCmap()
                # cmap is unicode_code -> glyph_name, we need the reverse
                for code, name in cmap.items():
                    unicode_lookup[name] = code
                font.close()
            except Exception as e:
                self.report({'WARNING'}, f"Could not load TTF for lookup: {e}")
        
        if not unicode_lookup:
            self.report({'ERROR'}, "No font file loaded or cmap empty. Import a font first.")
            return {'CANCELLED'}
        
        fixed_count = 0
        
        # Process ALL objects in the scene that end with _Guide
        for obj in context.scene.objects:
            if not obj.name.endswith("_Guide") and "_Guide." not in obj.name:
                continue
            
            # Extract glyph name: "zero_Guide" -> "zero", "A_Guide.001" -> "A"
            base_name = obj.name.split(".")[0]  # Strip .001 suffix
            glyph_name = base_name.replace("_Guide", "")
            
            # Get unicode from the TTF cmap lookup
            unicode_val = unicode_lookup.get(glyph_name)
            
            # Fix all children parented to this guide
            for child in obj.children:
                if child.type in ('CURVE', 'MESH', 'FONT'):
                    child["glyph_name"] = glyph_name
                    if unicode_val:
                        child["unicode"] = unicode_val
                    fixed_count += 1
        
        self.report({'INFO'}, f"Fixed {fixed_count} glyph objects ({len(unicode_lookup)} glyphs in cmap)")
        return {'FINISHED'}


class BF_OT_MergeIntoSelected(Operator):
    """Merge active curve into the main curve of each selected guide"""
    bl_idname = "bfont.merge_into_selected"
    bl_label = "Merge Into Selected Guides"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        active = context.active_object
        
        if not active:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}
        
        if active.type != 'CURVE':
            self.report({'ERROR'}, "Active object must be a curve")
            return {'CANCELLED'}
        
        # Find target guides (selected, excluding active and its parent)
        target_guides = []
        for obj in context.selected_objects:
            if obj == active or obj == active.parent:
                continue
            if obj.name.endswith("_Guide") or "_Guide." in obj.name:
                target_guides.append(obj)
        
        if not target_guides:
            self.report({'ERROR'}, "No target guides selected (select guides, make curve active)")
            return {'CANCELLED'}
        
        merged_count = 0
        
        for guide in target_guides:
            # Find the main curve child (the one whose name matches the guide minus _Guide)
            guide_base = guide.name.split(".")[0].replace("_Guide", "")
            main_curve = None
            for child in guide.children:
                if child.type == 'CURVE' and child.get("glyph_name"):
                    main_curve = child
                    break
            
            if not main_curve:
                # No main curve found, skip
                print(f"No main curve found for guide {guide.name}")
                continue
            
            # Copy splines from active curve into the main curve
            source_data = active.data
            target_data = main_curve.data
            
            # Take active's own transform (scale/rotation) but strip position
            # This moves the shape to the target guide's origin
            from mathutils import Matrix
            basis = active.matrix_basis.copy()
            basis.translation = (0, 0, 0)
            offset_matrix = basis
            
            for src_spline in source_data.splines:
                if src_spline.type == 'BEZIER':
                    new_spline = target_data.splines.new('BEZIER')
                    # Add points (spline starts with 1 point)
                    if len(src_spline.bezier_points) > 1:
                        new_spline.bezier_points.add(len(src_spline.bezier_points) - 1)
                    
                    for i, src_pt in enumerate(src_spline.bezier_points):
                        dst_pt = new_spline.bezier_points[i]
                        
                        # Transform points to guide's local space
                        co = offset_matrix @ src_pt.co
                        hl = offset_matrix @ src_pt.handle_left
                        hr = offset_matrix @ src_pt.handle_right
                        
                        dst_pt.co = co
                        dst_pt.handle_left = hl
                        dst_pt.handle_right = hr
                        dst_pt.handle_left_type = src_pt.handle_left_type
                        dst_pt.handle_right_type = src_pt.handle_right_type
                    
                    new_spline.use_cyclic_u = src_spline.use_cyclic_u
                
                elif src_spline.type == 'POLY':
                    new_spline = target_data.splines.new('POLY')
                    if len(src_spline.points) > 1:
                        new_spline.points.add(len(src_spline.points) - 1)
                    
                    for i, src_pt in enumerate(src_spline.points):
                        dst_pt = new_spline.points[i]
                        co = offset_matrix @ src_pt.co.to_3d()
                        dst_pt.co = (co.x, co.y, co.z, src_pt.co.w)
                    
                    new_spline.use_cyclic_u = src_spline.use_cyclic_u
            
            merged_count += 1
        
        self.report({'INFO'}, f"Merged curve into {merged_count} guides")
        return {'FINISHED'}
