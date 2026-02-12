import bpy
import os

# Try to import fonttools globally. If it fails, we handle it in the operators.
try:
    from fontTools.ttLib import TTFont
    from fontTools.pens.basePen import BasePen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.cu2quPen import Cu2QuPen
    FONTTOOLS_AVAILABLE = True
except ImportError:
    BasePen = object
    FONTTOOLS_AVAILABLE = False

def import_ttf_file(filepath, context):
    if not FONTTOOLS_AVAILABLE:
        report_missing_fonttools()
        return {'CANCELLED'}

    font = TTFont(filepath)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    
    # Store the filepath in scene property
    context.scene.bfont_filepath = filepath
    
    # Create a collection for the font
    font_name = os.path.basename(filepath)
    collection = bpy.data.collections.new(font_name)
    context.scene.collection.children.link(collection)
    
    # Get font metrics
    units_per_em = font['head'].unitsPerEm if 'head' in font else 1000
    ascender = font['hhea'].ascender if 'hhea' in font else units_per_em * 0.8
    descender = font['hhea'].descender if 'hhea' in font else -units_per_em * 0.2
    scale = 1.0 / units_per_em
    
    # Iterate over glyph order to be comprehensive
    glyph_order = font.getGlyphOrder()

    for glyph_name in glyph_order:
        if glyph_name not in glyph_set:
            continue

        pen = BlenderImportPen(glyph_set, glyph_name, scale)
        glyph = glyph_set[glyph_name]
        try:
            glyph.draw(pen)
            curve_data = pen.get_curve_data()
            
            # Create object even if curve is empty (for missing/empty glyphs)
            if not curve_data or len(curve_data.splines) == 0:
                # Create empty curve for glyphs with no contours
                curve_data = bpy.data.curves.new(name=glyph_name, type='CURVE')
                curve_data.dimensions = '2D'
                curve_data.fill_mode = 'BOTH'
            
            obj = bpy.data.objects.new(glyph_name, curve_data)
            collection.objects.link(obj)
            
            # Store original glyph name and unicode
            obj["glyph_name"] = glyph_name 
            
            unicode_code = None
            for code, name in cmap.items():
                if name == glyph_name:
                    obj["unicode"] = code
                    unicode_code = code
                    break
            
            # Create bounding guide mesh for THIS glyph
            guide_mesh = create_glyph_bounding_mesh(glyph_name, units_per_em, ascender, descender, scale)
            collection.objects.link(guide_mesh)
            
            # Both at same origin (lower left corner of glyph)
            obj.location = (0, 0, 0)
            guide_mesh.location = (0, 0, 0)
            
            # Parent the font char to the guide mesh
            obj.parent = guide_mesh
                
        except Exception as e:
            print(f"Error processing glyph {glyph_name}: {e}")

    return {'FINISHED'}


def create_glyph_bounding_mesh(glyph_name, units_per_em, ascender, descender, scale):
    """Create a mesh object with circle within square within square for a glyph"""
    import bmesh
    
    mesh = bpy.data.meshes.new(f"{glyph_name}_Guide")
    bm = bmesh.new()
    
    # Mesh offset
    offset_x = 0.5
    offset_y = -0.097
    
    # Calculate dimensions
    em_size = units_per_em * scale
    inner_size = em_size * 0.7
    circle_radius = em_size * 0.5
    
    # Center Y position (font origin is at baseline, typically y=0)
    center_y = (ascender + descender) / 2 * scale
    
    # Outer square (em square) with offset
    half_em = em_size / 2
    outer_verts = [
        bm.verts.new((offset_x + 0 - half_em, offset_y + center_y - half_em, 0)),
        bm.verts.new((offset_x + 0 + half_em, offset_y + center_y - half_em, 0)),
        bm.verts.new((offset_x + 0 + half_em, offset_y + center_y + half_em, 0)),
        bm.verts.new((offset_x + 0 - half_em, offset_y + center_y + half_em, 0))
    ]
    for i in range(4):
        bm.edges.new((outer_verts[i], outer_verts[(i+1)%4]))
    
    # Inner square with offset
    half_inner = inner_size / 2
    inner_verts = [
        bm.verts.new((offset_x + 0 - half_inner, offset_y + center_y - half_inner, 0)),
        bm.verts.new((offset_x + 0 + half_inner, offset_y + center_y - half_inner, 0)),
        bm.verts.new((offset_x + 0 + half_inner, offset_y + center_y + half_inner, 0)),
        bm.verts.new((offset_x + 0 - half_inner, offset_y + center_y + half_inner, 0))
    ]
    for i in range(4):
        bm.edges.new((inner_verts[i], inner_verts[(i+1)%4]))
    
    # Circle (approximate with 32 segments) with offset
    import math
    segments = 32
    circle_verts = []
    for i in range(segments):
        angle = (i / segments) * 2 * math.pi
        x = offset_x + circle_radius * math.cos(angle)
        y = offset_y + center_y + circle_radius * math.sin(angle)
        circle_verts.append(bm.verts.new((x, y, 0)))
    
    for i in range(segments):
        bm.edges.new((circle_verts[i], circle_verts[(i+1)%segments]))
    
    bm.to_mesh(mesh)
    bm.free()
    
    # Create object
    obj = bpy.data.objects.new(f"{glyph_name}_Guide", mesh)
    obj.display_type = 'WIRE'
    obj.show_wire = True
    obj.hide_render = True
    
    return obj


def export_ttf_file(filepath, context):
    if not FONTTOOLS_AVAILABLE:
        report_missing_fonttools()
        return {'CANCELLED'}
    
    # If no filepath provided, use stored one
    if not filepath and hasattr(context.scene, 'bfont_filepath'):
        filepath = context.scene.bfont_filepath
    
    if not filepath or not os.path.exists(filepath):
        def draw(self, context):
            self.layout.label(text="Target file must exist (export updates existing font).")
            self.layout.label(text="Import a font first to set the filepath.")
        bpy.context.window_manager.popup_menu(draw, title="Error", icon='ERROR')
        return {'CANCELLED'}

    font = TTFont(filepath)
    glyph_set = font.getGlyphSet()
    glyf_table = font['glyf']
    hmtx_table = font['hmtx'] # horiz metrics
    
    scale = 1.0
    if 'head' in font:
        units_per_em = font['head'].unitsPerEm
        scale = units_per_em 

    # Find all guide parents that have glyph children
    guide_parents = []
    for obj in context.scene.objects:
        if obj.children:
            for child in obj.children:
                if child.get("glyph_name"):
                    guide_parents.append((obj, child.get("glyph_name")))
                    break
    
    # Also find standalone glyph objects (not parented)
    for obj in context.scene.objects:
        if obj.get("glyph_name") and obj.parent is None:
            guide_parents.append((None, obj.get("glyph_name")))
        
    for guide_parent, glyph_name in guide_parents:
        if not glyph_name:
            continue
            
        # Draw blender curve to TTGlyphPen, wrapped with Cu2QuPen to convert cubic to quadratic
        tt_pen = TTGlyphPen(glyph_set)
        # Cu2QuPen converts cubic Bezier curves (from Blender) to quadratic curves (for TTF)
        pen = Cu2QuPen(tt_pen, max_err=1.0, reverse_direction=False)
        
        try:
            # Collect all children of the guide parent (or the standalone object)
            if guide_parent:
                children_to_export = list(guide_parent.children)
            else:
                # Find standalone glyph object
                children_to_export = [obj for obj in context.scene.objects 
                                      if obj.get("glyph_name") == glyph_name and obj.parent is None]
            
            # Process each child
            for child in children_to_export:
                curve_obj = convert_to_curve_if_needed(child, context)
                if curve_obj and curve_obj.type == 'CURVE':
                    write_blender_curve_to_pen(curve_obj, pen, scale)
                    
                    # Clean up temporary converted object
                    if curve_obj != child:
                        bpy.data.objects.remove(curve_obj)
            
            # Get the glyph object from the underlying TTGlyphPen
            new_glyph = tt_pen.glyph()
            
            # Update the glyph in the table
            glyf_table[glyph_name] = new_glyph
            
            # Update metrics if needed (width). 
            # Check first child for advance_width
            if children_to_export:
                first_child = children_to_export[0]
                if "advance_width" in first_child:
                    width = int(first_child["advance_width"] * scale)
                    lsb = hmtx_table[glyph_name][1]
                    hmtx_table[glyph_name] = (width, lsb)
                
        except Exception as e:
            print(f"Failed to export glyph {glyph_name}: {e}")

    font.save(filepath)
    return {'FINISHED'}


def convert_to_curve_if_needed(obj, context):
    """Convert mesh or text object to curve. Returns original if already a curve."""

    match obj.type:

        case 'CURVE':
            return obj

        case 'MESH':
            # Convert mesh to curve
            # Create a temporary copy and convert
            temp_mesh = obj.copy()
            temp_mesh.data = obj.data.copy()
            context.collection.objects.link(temp_mesh)
            # Select and convert
            bpy.ops.object.select_all(action='DESELECT')
            temp_mesh.select_set(True)
            context.view_layer.objects.active = temp_mesh
            bpy.ops.object.convert(target='CURVE')
            return temp_mesh

        case 'FONT':
            # Convert text to curve
            temp_text = obj.copy()
            temp_text.data = obj.data.copy()
            context.collection.objects.link(temp_text)
            # Select and convert
            bpy.ops.object.select_all(action='DESELECT')
            temp_text.select_set(True)
            context.view_layer.objects.active = temp_text
            bpy.ops.object.convert(target='CURVE')
            return temp_text

    return None


def report_missing_fonttools():
    def draw(self, context):
        self.layout.label(text="fonttools library not found.")
        self.layout.label(text="Please install it in Blender's python.")
    bpy.context.window_manager.popup_menu(draw, title="Error", icon='ERROR')


class BlenderImportPen(BasePen):
    def __init__(self, glyph_set, name, scale=1.0):
        super().__init__(glyph_set)
        self.curve_data = bpy.data.curves.new(name=name, type='CURVE')
        self.curve_data.dimensions = '2D'
        self.curve_data.fill_mode = 'BOTH'  # Fill the curves so they appear solid
        self.spline = None
        self.scale = scale

    def get_curve_data(self):
        return self.curve_data

    def _coord(self, pt):
        return (pt[0] * self.scale, pt[1] * self.scale, 0)

    def _moveTo(self, pt):
        self.spline = self.curve_data.splines.new('BEZIER')
        # Splines start with one point
        kp = self.spline.bezier_points[0]
        kp.co = self._coord(pt)
        kp.handle_left = self._coord(pt)
        kp.handle_right = self._coord(pt)
        kp.handle_left_type = 'FREE'
        kp.handle_right_type = 'FREE'

    def _lineTo(self, pt):
        if not self.spline: return
        self.spline.bezier_points.add(1)
        kp = self.spline.bezier_points[-1]
        kp.co = self._coord(pt)
        kp.handle_left = self._coord(pt)
        kp.handle_right = self._coord(pt)
        kp.handle_left_type = 'VECTOR'
        kp.handle_right_type = 'VECTOR'
        
        # Fix previous handle to point to this one linearly
        prev = self.spline.bezier_points[-2]
        prev.handle_right = prev.co
        prev.handle_right_type = 'VECTOR'
        kp.handle_left = kp.co


    def _qCurveToOne(self, pt1, pt2):
        # Quadratic curve segment (TTF uses these): current -> pt1 (control) -> pt2 (end)
        # Convert quadratic to cubic Bezier for Blender
        # Quadratic: P0, P1 (control), P2 (end)
        # Cubic: P0, C1, C2, P2 where:
        #   C1 = P0 + 2/3 * (P1 - P0)
        #   C2 = P2 + 2/3 * (P1 - P2)
        if not self.spline: return
        
        # Current point (P0)
        last_kp = self.spline.bezier_points[-1]
        p0 = (last_kp.co[0] / self.scale, last_kp.co[1] / self.scale)
        
        # Calculate cubic control points
        c1_x = p0[0] + (2.0/3.0) * (pt1[0] - p0[0])
        c1_y = p0[1] + (2.0/3.0) * (pt1[1] - p0[1])
        
        c2_x = pt2[0] + (2.0/3.0) * (pt1[0] - pt2[0])
        c2_y = pt2[1] + (2.0/3.0) * (pt1[1] - pt2[1])
        
        # Set handle_right of current point
        last_kp.handle_right = self._coord((c1_x, c1_y))
        last_kp.handle_right_type = 'FREE'
        
        # Add new point at pt2
        self.spline.bezier_points.add(1)
        kp = self.spline.bezier_points[-1]
        kp.co = self._coord(pt2)
        
        # Set handle_left of new point
        kp.handle_left = self._coord((c2_x, c2_y))
        kp.handle_left_type = 'FREE'
        kp.handle_right = self._coord(pt2)  # Default for next
        kp.handle_right_type = 'FREE'

    def _curveToOne(self, pt1, pt2, pt3):
        # Cubic curve segment: current -> pt1 -> pt2 -> pt3
        if not self.spline: return
        
        # Current point is the last one added
        last_kp = self.spline.bezier_points[-1]
        
        # The handle_right of the last point controls the exit towards pt1
        last_kp.handle_right = self._coord(pt1)
        last_kp.handle_right_type = 'FREE'
        
        # Add new point at pt3
        self.spline.bezier_points.add(1)
        kp = self.spline.bezier_points[-1]
        kp.co = self._coord(pt3)
        
        # The handle_left of the new point controls entry from pt2
        kp.handle_left = self._coord(pt2)
        kp.handle_left_type = 'FREE'
        kp.handle_right = self._coord(pt3) # Default for next
        kp.handle_right_type = 'FREE'

    def _closePath(self):
        if self.spline:
            self.spline.use_cyclic_u = True
            
    def _endPath(self):
        pass


def write_blender_curve_to_pen(obj, pen, scale):
    curve = obj.data
    if not curve: return
    
    # Use matrix_local to get transform relative to parent (not world position)
    # This way moving guide parents doesn't affect glyph coordinates
    # matrix_local = transform relative to parent
    # matrix_basis = object's own transform (ignoring parent)
    # We use matrix_basis if no parent, otherwise matrix_local
    if obj.parent:
        matrix = obj.matrix_local
    else:
        matrix = obj.matrix_basis
    
    def transform_point(pt):
        """Transform a point by the object's local matrix and apply scale"""
        transformed = matrix @ pt
        # Clamp to TTF valid range (-32768 to 32767) after scaling
        x = max(-32768, min(32767, int(transformed.x * scale)))
        y = max(-32768, min(32767, int(transformed.y * scale)))
        return (x, y)

    for spline in curve.splines:
        if spline.type != 'BEZIER':
            continue
            
        points = spline.bezier_points
        if len(points) == 0:
            continue

        # Start
        start_pt = transform_point(points[0].co)
        pen.moveTo(start_pt)
        
        for i in range(1, len(points)):
            p0 = points[i-1]
            p1 = points[i]
            
            # Check if this is a straight line or a curve
            # A segment is a line if both handles are in VECTOR mode or if handles match the points
            is_line = (p0.handle_right_type == 'VECTOR' and p1.handle_left_type == 'VECTOR')
            
            if is_line:
                # Straight line segment
                pen.lineTo(transform_point(p1.co))
            else:
                # Curved segment
                # p0 is start, p0.handle_right is c1, p1.handle_left is c2, p1.co is end
                c1 = transform_point(p0.handle_right)
                c2 = transform_point(p1.handle_left)
                end = transform_point(p1.co)
                
                pen.curveTo(c1, c2, end)
            
        if spline.use_cyclic_u:
            # Connect last to first
            p0 = points[-1]
            p1 = points[0]
            
            # Check if closing segment is a line or curve
            is_line = (p0.handle_right_type == 'VECTOR' and p1.handle_left_type == 'VECTOR')
            
            if is_line:
                pen.lineTo(transform_point(p1.co))
            else:
                c1 = transform_point(p0.handle_right)
                c2 = transform_point(p1.handle_left)
                end = transform_point(p1.co)
                
                pen.curveTo(c1, c2, end)
            pen.closePath()
        else:
            pen.endPath()
