# scripts/dxf_add_dim.py
import ezdxf, os, sys, json, math
from typing import List, Tuple, Dict, Optional
from collections import defaultdict

# ==============================================================================
# CÁC LỚP PHÂN TÍCH VÀ GHI KÍCH THƯỚC
# ==============================================================================

class GeometryAnalyzer:
    """Class to analyze DXF geometry and extract dimensionable features."""
    
    def __init__(self, tolerance=1e-6):
        self.tolerance = tolerance
        
    def get_line_endpoints(self, line):
        return (line.dxf.start.x, line.dxf.start.y), (line.dxf.end.x, line.dxf.end.y)
    
    def calculate_distance(self, point1, point2):
        return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)
    
    def calculate_angle(self, point1, point2, point3):
        vec1 = (point1[0] - point2[0], point1[1] - point2[1])
        vec2 = (point3[0] - point2[0], point3[1] - point2[1])
        dot_product = vec1[0] * vec2[0] + vec1[1] * vec2[1]
        mag1 = math.sqrt(vec1[0]**2 + vec1[1]**2)
        mag2 = math.sqrt(vec2[0]**2 + vec2[1]**2)
        if mag1 == 0 or mag2 == 0: return 0
        cos_angle = max(-1, min(1, dot_product / (mag1 * mag2)))
        return math.degrees(math.acos(cos_angle))
    
    def find_connected_lines(self, lines):
        connections = defaultdict(list)
        endpoints = {}
        for i, line in enumerate(lines):
            start, end = self.get_line_endpoints(line)
            start_rounded = (round(start[0], 4), round(start[1], 4))
            end_rounded = (round(end[0], 4), round(end[1], 4))
            if start_rounded not in endpoints: endpoints[start_rounded] = []
            if end_rounded not in endpoints: endpoints[end_rounded] = []
            endpoints[start_rounded].append(i)
            endpoints[end_rounded].append(i)
        for point, indices in endpoints.items():
            if len(indices) > 1:
                for i in indices:
                    for j in indices:
                        if i != j: connections[i].append(j)
        return connections

class DimensionPlacer:
    """Class to intelligently place dimensions on technical drawings."""
    
    def __init__(self, doc, offset_distance=10.0, text_height=2.5, dim_style="MY_ISO"):
        self.doc = doc
        self.msp = doc.modelspace()
        self.offset_distance = offset_distance
        self.text_height = text_height
        self.dim_style = dim_style
        self.analyzer = GeometryAnalyzer()
        
    def add_linear_dimension(self, start_point, end_point):
        dim = self.msp.add_aligned_dim(p1=start_point, p2=end_point, distance=self.offset_distance, dimstyle=self.dim_style)
        dim.render()
        return dim
    
    def add_angular_dimension(self, vertex_point, point1, point2):
        angle = self.analyzer.calculate_angle(point1, vertex_point, point2)
        if 10 < angle < 170:
            try:
                dim = self.msp.add_angular_dim_3p(base=vertex_point, p1=point1, p2=point2, dimstyle=self.dim_style)
                dim.render()
                return dim
            except ezdxf.DXFValueError: return None
        return None
    
    def add_diameter_dimension(self, center_point, radius):
        dim = self.msp.add_diameter_dim(center=center_point, radius=radius, angle=45, dimstyle=self.dim_style)
        dim.render()
        return dim
        
    # === SỬA LỖI: THAY ĐỔI CÁCH GỌI HÀM add_radius_dim ===
    def add_radial_dimension(self, center_point, radius, angle):
        """Add a radial dimension for arcs using radius and angle."""
        dim = self.msp.add_radius_dim(
            center=center_point,
            radius=radius,
            angle=angle, # Sử dụng angle thay vì point
            dimstyle=self.dim_style
        )
        dim.render()
        return dim

class AutoDimensioner:
    """Main class for automatic dimensioning of technical drawings."""
    
    def __init__(self, doc, config):
        self.doc = doc
        self.msp = doc.modelspace()
        self.analyzer = GeometryAnalyzer()
        self.config = config
        self.placer = DimensionPlacer(
            doc, 
            self.config['dimension_offset'], 
            self.config['text_height'],
            self.config['dim_style_name']
        )
    
    def dimension_drawing(self):
        """Automatically dimension the entire drawing."""
        print("[INFO] Bắt đầu quá trình ghi kích thước tự động...")
        
        entities = list(self.msp)
        lines = [e for e in entities if e.dxftype() == 'LINE']
        circles = [e for e in entities if e.dxftype() == 'CIRCLE']
        arcs = [e for e in entities if e.dxftype() == 'ARC']

        print(f"[INFO] Tìm thấy {len(lines)} đường, {len(circles)} đường tròn, {len(arcs)} cung.")
        
        if not lines and not circles and not arcs:
            print("[WARNING] Không tìm thấy đối tượng hình học nào để ghi kích thước.")
            return

        for line in lines:
            start, end = self.analyzer.get_line_endpoints(line)
            length = self.analyzer.calculate_distance(start, end)
            if length >= self.config['min_dimension_length']:
                self.placer.add_linear_dimension(start, end)
        
        if self.config['dimension_diameters']:
            for circle in circles:
                center = (circle.dxf.center.x, circle.dxf.center.y)
                radius = circle.dxf.radius
                self.placer.add_diameter_dimension(center, radius)
        
        # === SỬA LỖI: SỬA LOGIC GỌI HÀM add_radial_dimension ===
        if self.config['dimension_radii']:
            for arc in arcs:
                center = (arc.dxf.center.x, arc.dxf.center.y)
                radius = arc.dxf.radius
                # Tính góc ở giữa cung để đặt đường kích thước
                mid_angle = (arc.dxf.start_angle + arc.dxf.end_angle) / 2
                self.placer.add_radial_dimension(center, radius, mid_angle)
        
        print("[INFO] Hoàn tất ghi kích thước tự động.")

# ==============================================================================
# HÀM MAIN ĐỂ TÍCH HỢP VÀO PIPELINE
# ==============================================================================

def main():
    """Hàm chính để xử lý file DXF và thêm kích thước tự động."""
    print("--- Bắt đầu script dxf_add_dim.py (Phiên bản Advanced) ---")

    DXF_INPUT_PATH = "/app/output/step1_from_freecad.dxf"
    DXF_OUTPUT_PATH = "/app/output/step2_with_dims.dxf"

    try:
        doc = ezdxf.readfile(DXF_INPUT_PATH)
        
        with open("/app/config.json", 'r') as f: config_json = json.load(f)
        
        dimension_config = {
            'dimension_offset': float(config_json.get('DIMENSION_OFFSET', '15.0')),
            'text_height': float(config_json.get('DIMENSION_TEXT_HEIGHT', '2.5')),
            'min_dimension_length': float(config_json.get('MIN_DIMENSION_LENGTH', '5.0')),
            'max_dimensions_per_view': int(config_json.get('MAX_DIMENSIONS_PER_VIEW', '20')),
            'dimension_angles': config_json.get('DIMENSION_ANGLES', 'true').lower() == 'true',
            'dimension_radii': config_json.get('DIMENSION_RADII', 'true').lower() == 'true',
            'dimension_diameters': config_json.get('DIMENSION_DIAMETERS', 'true').lower() == 'true',
            'dim_style_name': "MY_ISO"
        }
        
        print(f"[INFO] Cấu hình ghi kích thước: {dimension_config}")
        
        # Thiết lập DimStyle
        if dimension_config['dim_style_name'] not in doc.dimstyles:
            dim_style = doc.dimstyles.new(name=dimension_config['dim_style_name'])
        else:
            dim_style = doc.dimstyles.get(dimension_config['dim_style_name'])
        
        dim_style.dxf.dimtxt = dimension_config['text_height']
        dim_style.dxf.dimasz = dimension_config['text_height'] * 0.8
        
        auto_dimensioner = AutoDimensioner(doc, dimension_config)
        auto_dimensioner.dimension_drawing()
        
        doc.saveas(DXF_OUTPUT_PATH)
        print("✅ [THÀNH CÔNG] Đã hoàn tất ghi kích thước nâng cao.")

    except Exception as e:
        print(f"❌ LỖI trong dxf_add_dim.py: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()