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
    scale = 1.0 / units_per_em
    
    # Create bounding box guides (circle within square within square)
    guides_parent, guide_objects = create_bounding_guides(font, scale)
    collection.objects.link(guides_parent)
    for guide_obj in guide_objects:
        collection.objects.link(guide_obj)
    
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
            
            # Store original glyph name
            obj["glyph_name"] = glyph_name 
            
            # Try to find unicode for identification
            for code, name in cmap.items():
                if name == glyph_name:
                    obj["unicode"] = code
                    break
            
            # Parent to guides
            obj.parent = guides_parent
                
        except Exception as e:
            print(f"Error processing glyph {glyph_name}: {e}")

    return {'FINISHED'}


def create_bounding_guides(font, scale):
    """Create circle within square within square as visual guides"""
    # Get font metrics
    units_per_em = font['head'].unitsPerEm if 'head' in font else 1000
    ascender = font['hhea'].ascender if 'hhea' in font else units_per_em * 0.8
    descender = font['hhea'].descender if 'hhea' in font else -units_per_em * 0.2
    
    # Create parent empty
    guides_parent = bpy.data.objects.new("BoundingGuides", None)
    guides_parent.empty_display_type = 'PLAIN_AXES'
    guides_parent.empty_display_size = 0.1 * scale
    
    guide_objects = []
    
    # Outer square (em square)
    outer_square = create_square_curve("EmSquare", units_per_em * scale, scale)
    outer_square.parent = guides_parent
    outer_square.location.y = (ascender + descender) / 2 * scale
    guide_objects.append(outer_square)
    
    # Inner square (smaller reference)
    inner_square = create_square_curve("InnerSquare", units_per_em * 0.7 * scale, scale)
    inner_square.parent = guides_parent
    inner_square.location.y = (ascender + descender) / 2 * scale
    guide_objects.append(inner_square)
    
    # Circle (for reference)
    circle = create_circle_curve("Circle", units_per_em * 0.5 * scale, scale)
    circle.parent = guides_parent
    circle.location.y = (ascender + descender) / 2 * scale
    guide_objects.append(circle)
    
    return guides_parent, guide_objects


def create_square_curve(name, size, scale):
    """Create a square curve object"""
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '2D'
    curve_data.fill_mode = 'NONE'
    
    spline = curve_data.splines.new('POLY')
    spline.points.add(3)  # 4 points total (including the first one)
    
    half = size / 2
    spline.points[0].co = (-half, -half, 0, 1)
    spline.points[1].co = (half, -half, 0, 1)
    spline.points[2].co = (half, half, 0, 1)
    spline.points[3].co = (-half, half, 0, 1)
    spline.use_cyclic_u = True
    
    obj = bpy.data.objects.new(name, curve_data)
    obj.show_wire = True
    obj.display_type = 'WIRE'
    
    return obj


def create_circle_curve(name, radius, scale):
    """Create a circle curve object"""
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '2D'
    curve_data.fill_mode = 'NONE'
    
    spline = curve_data.splines.new('BEZIER')
    # Circle needs 4 bezier points
    spline.bezier_points.add(3)
    
    # Magic number for circle approximation with bezier
    magic = 0.551915024494
    
    points = [
        (radius, 0),
        (0, radius),
        (-radius, 0),
        (0, -radius)
    ]
    
    for i, (x, y) in enumerate(points):
        bp = spline.bezier_points[i]
        bp.co = (x, y, 0)
        bp.handle_left_type = 'FREE'
        bp.handle_right_type = 'FREE'
        
        # Set handles for circle
        if i == 0:  # Right
            bp.handle_left = (x, -y * magic, 0)
            bp.handle_right = (x, y * magic, 0)
        elif i == 1:  # Top
            bp.handle_left = (x * magic, y, 0)
            bp.handle_right = (-x * magic, y, 0)
        elif i == 2:  # Left
            bp.handle_left = (x, y * magic, 0)
            bp.handle_right = (x, -y * magic, 0)
        elif i == 3:  # Bottom
            bp.handle_left = (-x * magic, y, 0)
            bp.handle_right = (x * magic, y, 0)
    
    spline.use_cyclic_u = True
    
    obj = bpy.data.objects.new(name, curve_data)
    obj.show_wire = True
    obj.display_type = 'WIRE'
    
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

    # Determine which objects to export
    objects_to_process = []
    if context.selected_objects:
        objects_to_process = context.selected_objects
    else:
        # If nothing selected, try to export all objects in the active collection that look like glyphs
        objects_to_process = context.collection.objects
        
    for obj in objects_to_process:
        if obj.type != 'CURVE':
            continue
            
        glyph_name = obj.get("glyph_name")
        if not glyph_name:
            continue
            
        # Draw blender curve to TTGlyphPen, wrapped with Cu2QuPen to convert cubic to quadratic
        tt_pen = TTGlyphPen(glyph_set)
        # Cu2QuPen converts cubic Bezier curves (from Blender) to quadratic curves (for TTF)
        pen = Cu2QuPen(tt_pen, max_err=1.0, reverse_direction=False)
        
        try:
            write_blender_curve_to_pen(obj, pen, scale)
            
            # Get the glyph object from the underlying TTGlyphPen
            new_glyph = tt_pen.glyph()
            
            # Update the glyph in the table
            glyf_table[glyph_name] = new_glyph
            
            # Update metrics if needed (width). 
            if "advance_width" in obj:
                width = int(obj["advance_width"] * scale)
                lsb = hmtx_table[glyph_name][1] # preserve LSB? or recalculate?
                hmtx_table[glyph_name] = (width, lsb)
                
        except Exception as e:
            print(f"Failed to export glyph {glyph_name}: {e}")

    font.save(filepath)
    return {'FINISHED'}


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

    for spline in curve.splines:
        if spline.type != 'BEZIER':
            continue
            
        points = spline.bezier_points
        if len(points) == 0:
            continue

        # Start
        start_pt = points[0].co
        pen.moveTo((start_pt.x * scale, start_pt.y * scale))
        
        for i in range(1, len(points)):
            p0 = points[i-1]
            p1 = points[i]
            
            # Check if this is a straight line or a curve
            # A segment is a line if both handles are in VECTOR mode or if handles match the points
            is_line = (p0.handle_right_type == 'VECTOR' and p1.handle_left_type == 'VECTOR')
            
            if is_line:
                # Straight line segment
                pen.lineTo((p1.co.x * scale, p1.co.y * scale))
            else:
                # Curved segment
                # p0 is start, p0.handle_right is c1, p1.handle_left is c2, p1.co is end
                c1 = p0.handle_right
                c2 = p1.handle_left
                end = p1.co
                
                pen.curveTo(
                    (c1.x * scale, c1.y * scale),
                    (c2.x * scale, c2.y * scale),
                    (end.x * scale, end.y * scale)
                )
            
        if spline.use_cyclic_u:
            # Connect last to first
            p0 = points[-1]
            p1 = points[0]
            
            # Check if closing segment is a line or curve
            is_line = (p0.handle_right_type == 'VECTOR' and p1.handle_left_type == 'VECTOR')
            
            if is_line:
                pen.lineTo((p1.co.x * scale, p1.co.y * scale))
            else:
                c1 = p0.handle_right
                c2 = p1.handle_left
                end = p1.co
                
                pen.curveTo(
                    (c1.x * scale, c1.y * scale),
                    (c2.x * scale, c2.y * scale),
                    (end.x * scale, end.y * scale)
                )
            pen.closePath()
        else:
            pen.endPath()
