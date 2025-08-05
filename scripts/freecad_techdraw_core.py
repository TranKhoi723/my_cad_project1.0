# scripts/freecad_techdraw_enhanced.py
import sys, os, time, math, json, traceback
import FreeCAD as App
import Part, TechDraw
from FreeCAD import Vector, Units, Rotation

class PaperSizeManager:
    """Manages standard paper sizes and their parameters"""
    
    PAPER_SIZES = {
        'A0': {'width': 1189.0, 'height': 841.0, 'margin': 25.0},
        'A1': {'width': 841.0, 'height': 594.0, 'margin': 20.0},
        'A2': {'width': 594.0, 'height': 420.0, 'margin': 15.0},
        'A3': {'width': 420.0, 'height': 297.0, 'margin': 10.0},
        'A4': {'width': 297.0, 'height': 210.0, 'margin': 8.0},
        'A5': {'width': 210.0, 'height': 148.0, 'margin': 5.0}
    }
    
    @classmethod
    def get_paper_info(cls, template_file):
        """Retrieves paper size information from the template file name"""
        for size_name, info in cls.PAPER_SIZES.items():
            if size_name.lower() in template_file.lower():
                return size_name, info
        # Default to A3 if not identified
        return 'A3', cls.PAPER_SIZES['A3']

class AutoScaleCalculator:
    """Calculates automatic scale based on paper size and part dimensions"""
    
    def __init__(self, part, paper_info):
        self.part = part
        self.paper_info = paper_info
        self.bbox = self._get_bounding_box()
    
    def _get_bounding_box(self):
        """Gets the bounding box of the part"""
        try:
            return self.part.Shape.BoundBox
        except:
            # Fallback bbox if not obtainable
            return type('BoundBox', (), {
                'XMin': -50, 'XMax': 50,
                'YMin': -50, 'YMax': 50,
                'ZMin': -50, 'ZMax': 50
            })()
    
    def calculate_optimal_scale(self, current_scale=1.0):
        """Calculates the optimal scale"""
        # Actual part dimensions
        part_dims = {
            'length': self.bbox.XMax - self.bbox.XMin,
            'width': self.bbox.YMax - self.bbox.YMin,
            'height': self.bbox.ZMax - self.bbox.ZMin
        }
        
        # Estimate space needed for layout (3 views + iso)
        required_width = part_dims['length'] + part_dims['width'] + 100
        required_height = part_dims['height'] + part_dims['width'] + 100
        
        # Usable space
        usable_width = self.paper_info['width'] - 2 * self.paper_info['margin'] - 200
        usable_height = self.paper_info['height'] - 2 * self.paper_info['margin'] - 100
        
        # Calculate required scale
        scale_x = usable_width / required_width if required_width > 0 else 1.0
        scale_y = usable_height / required_height if required_height > 0 else 1.0
        
        optimal_scale = min(scale_x, scale_y) * 0.8  # 80% for buffer
        
        # Round down to a standard scale
        standard_scales = [0.05, 0.1, 0.2, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
        for scale in reversed(standard_scales):
            if optimal_scale >= scale:
                return scale
        
        return 0.05

class TechDrawEnhancer:
    """Enhances TechDraw views with centerlines, hidden lines, etc."""
    
    def __init__(self, doc, page):
        self.doc = doc
        self.page = page
    
    def add_centerlines_to_view(self, view, part):
        """Adds centerlines for circular features/holes"""
        try:
            # Find circular features in the part
            circular_features = self._find_circular_features(part, view.Direction)
            
            for feature in circular_features:
                centerline = self.doc.addObject("TechDraw::DrawViewSymbol", f"CenterLine_{feature['name']}")
                centerline.Symbol = self._create_centerline_symbol(feature['center'], feature['radius'])
                # Add centerline to the page, not the view
                self.page.addView(centerline)
                
            print(f"[INFO] Added {len(circular_features)} centerlines to view {view.Name}")
            
        except Exception as e:
            print(f"[WARNING] Error adding centerlines: {e}")
    
    def _find_circular_features(self, part, view_direction):
        """Finds circular features in the part based on view direction"""
        features = []
        
        try:
            # Analyze part faces
            for i, face in enumerate(part.Shape.Faces):
                if hasattr(face.Surface, 'Radius'):  # Cylindrical surface
                    face_normal = face.normalAt(0, 0)
                    dot_product = abs(face_normal.dot(view_direction))
                    
                    if dot_product > 0.9:  # Nearly perpendicular
                        center = face.CenterOfMass
                        radius = face.Surface.Radius
                        
                        features.append({
                            'name': f"Circular_{i}",
                            'center': self._project_point(center, view_direction),
                            'radius': radius
                        })
                        
        except Exception as e:
            print(f"[DEBUG] Error analyzing circular features: {e}")
        
        return features
    
    def _project_point(self, point, view_direction):
        """Projects a 3D point onto a 2D plane"""
        if abs(view_direction.z) > 0.9:  # Top view
            return (point.x, point.y)
        elif abs(view_direction.y) > 0.9:  # Front view  
            return (point.x, point.z)
        else:  # Right view
            return (point.y, point.z)
    
    def _create_centerline_symbol(self, center, radius):
        """Creates a symbol for the centerline"""
        cx, cy = center
        size = radius * 1.5
        
        svg_content = f'''
        <g>
            <line x1="{cx-size}" y1="{cy}" x2="{cx+size}" y2="{cy}" 
                  stroke="black" stroke-width="0.25" stroke-dasharray="2,1"/>
            <line x1="{cx}" y1="{cy-size}" x2="{cx}" y2="{cy+size}" 
                  stroke="black" stroke-width="0.25" stroke-dasharray="2,1"/>
        </g>
        '''
        return svg_content
    
    def enable_hidden_lines(self, view):
        """Activates hidden line display"""
        try:
            view.HardHidden = True
            view.SmoothHidden = True
            view.SeamHidden = True
            view.IsoHidden = True
            
            print(f"[INFO] Enabled hidden lines for view {view.Name}")
            
        except Exception as e:
            print(f"[WARNING] Error enabling hidden lines: {e}")
    
    def add_section_lines(self, view, part):
        """Adds hatching for section view if needed"""
        try:
            if hasattr(view, 'SectionOrigin'):
                hatch = self.doc.addObject("TechDraw::DrawHatch", f"Hatch_{view.Name}")
                hatch.Source = [view]
                hatch.HatchPattern = "ANSI31"
                hatch.HatchScale = 1.0
                view.addView(hatch)
                
                print(f"[INFO] Added hatching for section view {view.Name}")
                
        except Exception as e:
            print(f"[WARNING] Error adding section lines: {e}")

class SmartLayoutManager:
    """Manages smart layout of views"""
    
    def __init__(self, paper_info, config):
        self.paper_width = paper_info['width']
        self.paper_height = paper_info['height']
        self.margin = paper_info['margin']
        self.config = config
        self.layout_mode = config.get('LAYOUT_MODE', 'auto')
    
    def calculate_layout(self, views_data, scale):
        """Calculates optimal positions for views"""
        if self.layout_mode == 'manual':
            return self._manual_layout(views_data, scale)
        else:
            return self._auto_layout(views_data, scale)
    
    def _auto_layout(self, views_data, scale):
        """Automatic layout according to technical standards (Third Angle Projection)"""
        layout = {}
        
        front_w = views_data['Front']['width'] * scale
        front_h = views_data['Front']['height'] * scale
        top_w = views_data['Top']['width'] * scale
        top_h = views_data['Top']['height'] * scale
        right_w = views_data['Right']['width'] * scale
        right_h = views_data['Right']['height'] * scale
        iso_w = views_data['Iso']['width'] * scale
        iso_h = views_data['Iso']['height'] * scale
        
        spacing = float(self.config.get('MIN_SPACING', '30.0'))
        
        orthogonal_block_width = max(front_w, top_w) + spacing + right_w
        orthogonal_block_height = top_h + spacing + front_h
        
        usable_width = self.paper_width - 2 * self.margin
        usable_height = self.paper_height - 2 * self.margin
        
        block_start_x = self.margin + (usable_width - orthogonal_block_width) / 2
        block_start_y = self.margin + (usable_height - orthogonal_block_height) / 2
        
        # Position views relative to block_start
        front_x_pos = block_start_x + max(front_w, top_w) / 2
        front_y_pos = block_start_y + top_h + spacing + front_h / 2
        layout['Front'] = {'x': front_x_pos, 'y': front_y_pos}
        
        layout['Top'] = {
            'x': front_x_pos,
            'y': block_start_y + top_h / 2
        }
        
        layout['Right'] = {
            'x': block_start_x + max(front_w, top_w) + spacing + right_w / 2,
            'y': front_y_pos
        }
        
        layout['Iso'] = {
            'x': self.paper_width - self.margin - iso_w / 2,
            'y': self.paper_height - self.margin - iso_h / 2
        }
        
        return layout
    
    def _manual_layout(self, views_data, scale):
        """Manual layout according to config"""
        layout = {}
        manual_positions = self.config.get('MANUAL_POSITIONS', {})
        
        for view_name in views_data.keys():
            if view_name in manual_positions:
                layout[view_name] = manual_positions[view_name]
            else:
                layout[view_name] = {'x': 100, 'y': 100}
        
        return layout

def main():
    """Main function with enhanced TechDraw"""
    doc = None
    try:
        print("[INFO] Starting Enhanced FreeCAD TechDraw...")
        
        with open("/app/config.json", 'r') as f:
            config = json.load(f)
        
        template_path = os.path.join("/app/templates", config.get("TEMPLATE_FILE", ""))
        step_file_path = os.path.join("/app/input", config["INPUT_FILE"])
        
        print(f"[INFO] STEP file: {step_file_path}")
        print(f"[INFO] Template: {template_path}")
        
        if not os.path.exists(step_file_path):
            raise FileNotFoundError(f"STEP file not found: {step_file_path}")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        doc = App.newDocument("EnhancedDrawing")
        Part.insert(step_file_path, doc.Name)
        doc.recompute()
        part = doc.Objects[0]
        
        print(f"[INFO] Part imported: {part.Name}")
        
        page = doc.addObject("TechDraw::DrawPage", "Page")
        template = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
        template.Template = template_path
        page.Template = template
        doc.recompute()
        
        paper_name, paper_info = PaperSizeManager.get_paper_info(template_path)
        print(f"[INFO] Paper size: {paper_name} ({paper_info['width']}x{paper_info['height']}mm)")
        
        auto_scale_enabled = config.get('AUTO_SCALE', 'false').lower() == 'true'
        if auto_scale_enabled:
            scale_calculator = AutoScaleCalculator(part, paper_info)
            optimal_scale = scale_calculator.calculate_optimal_scale()
            print(f"[INFO] Auto-calculated scale: {optimal_scale}")
            scale_value = optimal_scale
        else:
            scale_value = float(config.get("SCALE", "1.0"))
            print(f"[INFO] Using manual scale: {scale_value}")
        
        directions = {
            "Front": Vector(0, -1, 0),
            "Top": Vector(0, 0, -1),
            "Right": Vector(-1, 0, 0),
            "Iso": Vector(1, 1, 1).normalize()
        }
        
        views = {}
        for name, direction in directions.items():
            view = doc.addObject("TechDraw::DrawViewPart", f"{name}View")
            view.Source = [part]
            view.Direction = direction
            view.ScaleType = "Custom"
            view.Scale = scale_value
            page.addView(view)
            views[name] = view
            
            print(f"[INFO] Created {name} view")
        
        doc.recompute()
        time.sleep(2) # Add a delay for FreeCAD to complete processing
        
        enhancer = TechDrawEnhancer(doc, page)
        
        for view_name, view in views.items():
            enhancer.enable_hidden_lines(view)
            if view_name in ['Front', 'Top', 'Right']:
                enhancer.add_centerlines_to_view(view, part)
            enhancer.add_section_lines(view, part)
        
        doc.recompute()
        
        def estimate_view_bounds(obj, direction, scale):
            """Estimates view bounds"""
            try:
                bbox = obj.Shape.BoundBox
                
                # Projection logic
                if abs(direction.z) > 0.9:  # Top view
                    w, h = bbox.XMax - bbox.XMin, bbox.YMax - bbox.YMin
                elif abs(direction.y) > 0.9:  # Front view
                    w, h = bbox.XMax - bbox.XMin, bbox.ZMax - bbox.ZMin
                elif abs(direction.x) > 0.9:  # Right view
                    w, h = bbox.YMax - bbox.YMin, bbox.ZMax - bbox.ZMin
                else: # Isometric view, use simple estimation
                    w = (bbox.XMax - bbox.XMin) + (bbox.YMax - bbox.YMin)
                    h = (bbox.ZMax - bbox.ZMin) + (bbox.YMax - bbox.YMin)
                
                return w * scale, h * scale
                
            except Exception as e:
                print(f"[WARNING] Error estimating bounds: {e}")
                return 100, 100
        
        views_data = {}
        for view_name, direction in directions.items():
            width, height = estimate_view_bounds(part, direction, scale_value)
            views_data[view_name] = {
                'width': width,
                'height': height
            }
        
        layout_manager = SmartLayoutManager(paper_info, config)
        layout = layout_manager.calculate_layout(views_data, scale_value)
        
        for view_name, position in layout.items():
            if view_name in views:
                views[view_name].X = Units.Quantity(f"{position['x']} mm")
                views[view_name].Y = Units.Quantity(f"{position['y']} mm")
                print(f"[INFO] {view_name} view positioned at ({position['x']:.1f}, {position['y']:.1f})")
        
        doc.recompute()
        
        # Fix output file name to match dxf_add_dim.py input file
        dxf_output_path = "/app/output/step1_from_freecad.dxf"
        TechDraw.writeDXFPage(page, dxf_output_path)
        
        print(f"✅ [SUCCESS] Enhanced TechDraw completed!")
        print(f"✅ DXF exported: {dxf_output_path}")
        print(f"   - Paper size: {paper_name}")
        print(f"   - Scale: {scale_value}")
        print(f"   - Layout: {config.get('LAYOUT_MODE', 'auto')}")
        print(f"   - Hidden lines: Enabled")
        print(f"   - Centerlines: Added")
        
    except Exception as e:
        sys.stderr.write(f"\n❌ ERROR in freecad_techdraw_enhanced.py: {e}\n")
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'doc' in locals() and doc:
            App.closeDocument(doc.Name)

if __name__ == "__main__":
    main()
