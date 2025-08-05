# scripts/dxf_add_dim_enhanced.py
import ezdxf
import json
import math
import sys
from pathlib import Path
from ezdxf.math import Vec2, Vec3
from ezdxf.tools.standards import setup_dimstyle
from collections import defaultdict
from typing import List, Tuple, Dict, Set, Optional

class StandardDimStyles:
    """Creates standard dimension styles based on ISO and ANSI."""
    
    @staticmethod
    def create_iso_dimstyle(doc, name="ISO_STANDARD"):
        """Creates an ISO-compliant dimension style."""
        if name in doc.dimstyles:
            return doc.dimstyles.get(name)
            
        dimstyle = doc.dimstyles.new(name)
        
        # ISO standard settings
        dimstyle.dxf.dimtxt = 2.5      # Text height
        dimstyle.dxf.dimasz = 2.5      # Arrow size
        dimstyle.dxf.dimexe = 1.25     # Extension line extension
        dimstyle.dxf.dimexo = 0.625    # Extension line offset
        dimstyle.dxf.dimgap = 0.625    # Gap around text
        dimstyle.dxf.dimtad = 1        # Text above dimension line
        dimstyle.dxf.dimtih = 0        # Text inside horizontal
        dimstyle.dxf.dimtoh = 0        # Text outside horizontal
        dimstyle.dxf.dimtxsty = "Standard"
        dimstyle.dxf.dimldrblk = "NONE"  # Leader block
        dimstyle.dxf.dimblk = "NONE"     # Arrow block
        dimstyle.dxf.dimblk1 = "NONE"    # First arrow
        dimstyle.dxf.dimblk2 = "NONE"    # Second arrow
        dimstyle.dxf.dimclrd = 0         # Dimension line color
        dimstyle.dxf.dimclre = 0         # Extension line color
        dimstyle.dxf.dimclrt = 0         # Text color
        
        return dimstyle
    
    @staticmethod
    def create_ansi_dimstyle(doc, name="ANSI_STANDARD"):
        """Creates an ANSI/ASME-compliant dimension style."""
        if name in doc.dimstyles:
            return doc.dimstyles.get(name)
            
        dimstyle = doc.dimstyles.new(name)
        
        # ANSI standard settings
        dimstyle.dxf.dimtxt = 3.0      # Text height
        dimstyle.dxf.dimasz = 3.0      # Arrow size
        dimstyle.dxf.dimexe = 1.5      # Extension line extension
        dimstyle.dxf.dimexo = 1.5      # Extension line offset
        dimstyle.dxf.dimgap = 1.5      # Text gap
        dimstyle.dxf.dimtad = 0        # Text centered on dimension line
        dimstyle.dxf.dimtih = 1        # Text inside horizontal
        dimstyle.dxf.dimtoh = 1        # Text outside horizontal
        dimstyle.dxf.dimunit = 2       # Decimal units
        dimstyle.dxf.dimdec = 2        # Decimal places
        
        return dimstyle

class GeometryClassifier:
    """Classifies and groups geometric entities by projection view."""
    
    def __init__(self, tolerance=5.0):
        self.tolerance = tolerance
        
    def classify_by_projection(self, entities):
        """Classifies entities into projection views based on their spatial location."""
        projections = {
            'front': [],
            'top': [],
            'right': [],
            'iso': []
        }
        
        # Calculate bounding box of all entities
        all_points = []
        for entity in entities:
            if entity.dxftype() == 'LINE':
                all_points.extend([Vec2(entity.dxf.start), Vec2(entity.dxf.end)])
            elif entity.dxftype() in ['CIRCLE', 'ARC']:
                center = Vec2(entity.dxf.center)
                radius = entity.dxf.radius
                all_points.extend([
                    Vec2(center.x - radius, center.y - radius),
                    Vec2(center.x + radius, center.y + radius)
                ])
        
        if not all_points:
            return projections
            
        min_x = min(p.x for p in all_points)
        max_x = max(p.x for p in all_points)
        min_y = min(p.y for p in all_points)
        max_y = max(p.y for p in all_points)
        
        # Divide space into regions
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        for entity in entities:
            entity_center = self._get_entity_center(entity)
            
            # Classify based on relative position
            if entity_center.x < center_x and entity_center.y < center_y:
                projections['front'].append(entity)
            elif entity_center.x < center_x and entity_center.y > center_y:
                projections['top'].append(entity)
            elif entity_center.x > center_x and entity_center.y < center_y:
                projections['right'].append(entity)
            else:
                projections['iso'].append(entity)
                
        return projections
    
    def _get_entity_center(self, entity):
        """Gets the center point of an entity."""
        if entity.dxftype() == 'LINE':
            start = Vec2(entity.dxf.start)
            end = Vec2(entity.dxf.end)
            return (start + end) / 2
        elif entity.dxftype() in ['CIRCLE', 'ARC']:
            return Vec2(entity.dxf.center)
        return Vec2(0, 0)

class EdgeConnectivityAnalyzer:
    """Analyzes connectivity between edges to handle discrete segments."""
    
    def __init__(self, tolerance=1e-3):
        self.tolerance = tolerance
    
    def group_connected_edges(self, lines):
        """Groups connected lines into chains."""
        if not lines:
            return []
        
        # Create connection graph
        connections = defaultdict(list)
        endpoints = defaultdict(list)
        
        # Map endpoints with indices
        for i, line in enumerate(lines):
            start = self._round_point(Vec2(line.dxf.start))
            end = self._round_point(Vec2(line.dxf.end))
            
            endpoints[start].append(i)
            endpoints[end].append(i)
        
        # Create connections
        for point, line_indices in endpoints.items():
            for i in line_indices:
                for j in line_indices:
                    if i != j:
                        connections[i].append(j)
        
        # Find chains
        visited = set()
        chains = []
        
        for i, line in enumerate(lines):
            if i not in visited:
                chain = self._build_chain(i, lines, connections, visited)
                if len(chain) > 1:  # Only save chains with > 1 element
                    chains.append(chain)
        
        return chains
    
    def _round_point(self, point):
        """Rounds a point for comparison."""
        return (round(point.x / self.tolerance) * self.tolerance,
                round(point.y / self.tolerance) * self.tolerance)
    
    def _build_chain(self, start_idx, lines, connections, visited):
        """Builds a chain from a starting point."""
        chain = []
        stack = [start_idx]
        
        while stack:
            current = stack.pop()
            if current in visited:
                continue
                
            visited.add(current)
            chain.append(current)
            
            # Add unvisited connected lines
            for neighbor in connections[current]:
                if neighbor not in visited:
                    # Check if they form a continuous line
                    if self._lines_are_continuous(lines[current], lines[neighbor]):
                        stack.append(neighbor)
        
        return chain
    
    def _lines_are_continuous(self, line1, line2):
        """Checks if two lines are continuous (same or nearly same direction)."""
        # Direction vectors
        d1 = Vec2(line1.dxf.end) - Vec2(line1.dxf.start)
        d2 = Vec2(line2.dxf.end) - Vec2(line2.dxf.start)
        
        if d1.magnitude < self.tolerance or d2.magnitude < self.tolerance:
            return False
        
        # Normalize
        d1_norm = d1.normalize()
        d2_norm = d2.normalize()
        
        # Check angle between vectors (allow same or opposite direction)
        dot_product = abs(d1_norm.dot(d2_norm))
        return dot_product > 0.9  # cos(~25°)
    
    def get_chain_total_length(self, chain, lines):
        """Calculates the total length of a chain."""
        total_length = 0
        for idx in chain:
            line = lines[idx]
            start = Vec2(line.dxf.start)
            end = Vec2(line.dxf.end)
            total_length += (end - start).magnitude
        return total_length
    
    def get_chain_endpoints(self, chain, lines):
        """Gets the start and end points of a chain."""
        if not chain:
            return None, None
        
        first_line = lines[chain[0]]
        last_line = lines[chain[-1]]
        
        # Find true endpoints of the chain
        all_points = []
        point_count = defaultdict(int)
        
        for idx in chain:
            line = lines[idx]
            start = self._round_point(Vec2(line.dxf.start))
            end = self._round_point(Vec2(line.dxf.end))
            point_count[start] += 1
            point_count[end] += 1
            all_points.extend([start, end])
        
        # Endpoints are points that appear only once
        endpoints = [point for point, count in point_count.items() if count == 1]
        
        if len(endpoints) >= 2:
            return Vec2(endpoints[0]), Vec2(endpoints[1])
        
        # Fallback
        return Vec2(first_line.dxf.start), Vec2(last_line.dxf.end)
   
class SmartDimensioner:
    """Intelligent system for adding standards-compliant dimensions."""
    
    def __init__(self, msp, config, standard='ISO'):
        self.msp = msp
        self.config = config
        self.standard = standard
        self.tolerance = 1e-6
        self.setup_dimstyles()
        self.dimensioned_features = set()  # Tracks already dimensioned features
        self.dimensioned_radii = set()        
        self.dimensioned_diameters = set()

    def setup_dimstyles(self):
        """Sets up dimension styles based on the chosen standard."""
        doc = self.msp.doc
        
        if self.standard == 'ISO':
            self.dimstyle = StandardDimStyles.create_iso_dimstyle(doc)
            self.style_name = "ISO_STANDARD"
        else:
            self.dimstyle = StandardDimStyles.create_ansi_dimstyle(doc)
            self.style_name = "ANSI_STANDARD"
    
    def dimension_projections(self, projections):
        """Dimensions all orthogonal projections."""
        dimension_count = 0
        
        # Prioritize dimensioning: Front > Top > Right > Iso
        priority_order = ['front', 'top', 'right', 'iso']
        
        for proj_name in priority_order:
            if proj_name in projections and projections[proj_name]:
                print(f"[INFO] Dimensioning {proj_name.upper()} view...")
                count = self._dimension_single_projection(projections[proj_name], proj_name)
                dimension_count += count
                print(f"[INFO] Added {count} dimensions to {proj_name.upper()} view.")
        
        return dimension_count
    
    def _dimension_single_projection(self, entities, projection_name):
        """Dimensions a single projection view."""
        lines = [e for e in entities if e.dxftype() == 'LINE']
        circles = [e for e in entities if e.dxftype() == 'CIRCLE']
        arcs = [e for e in entities if e.dxftype() == 'ARC']
        
        dimension_count = 0
        
        # 1. Dimension horizontal and vertical lines
        horizontal_lines, vertical_lines, other_lines = self._classify_lines(lines)
        
        # Dimension horizontal lines (priority)
        if projection_name in ['front', 'top']:
            dimension_count += self._dimension_aligned_lines(horizontal_lines, 'horizontal')
        
        # Dimension vertical lines
        if projection_name in ['front', 'right']:
            dimension_count += self._dimension_aligned_lines(vertical_lines, 'vertical')
        
        # 2. Dimension circles and arcs
        if self.config.get('dimension_diameters', True):
            for circle in circles:
                self._add_diameter_dimension(circle)
                dimension_count += 1
        
        if self.config.get('dimension_radii', True):
            for arc in arcs:
                self._add_radius_dimension(arc)
                dimension_count += 1
        
        # 3. Dimension important angles
        if self.config.get('dimension_angles', True):
            angle_count = self._dimension_angles(other_lines)
            dimension_count += angle_count
        
        return dimension_count
    
    def _classify_lines(self, lines):
        """Classifies lines by orientation."""
        horizontal = []
        vertical = []
        other = []
        
        for line in lines:
            start = Vec2(line.dxf.start)
            end = Vec2(line.dxf.end)
            direction = end - start
            
            if abs(direction.y) < self.tolerance:  # Horizontal line
                horizontal.append(line)
            elif abs(direction.x) < self.tolerance:  # Vertical line
                vertical.append(line)
            else:
                other.append(line)
        
        return horizontal, vertical, other
    
    def _dimension_aligned_lines(self, lines, orientation):
        """Dimensions aligned lines."""
        if not lines:
            return 0
        
        dimension_count = 0
        processed_lengths = set()
        
        for line in lines:
            start = Vec2(line.dxf.start)
            end = Vec2(line.dxf.end)
            length = (end - start).magnitude
            
            # Check minimum length
            if length < self.config.get('min_dimension_length', 5.0):
                continue
            
            # Avoid duplicate dimensions for the same length
            length_key = round(length, 2)
            if length_key in processed_lengths:
                continue
            
            # Calculate dimension placement
            offset_distance = self.config.get('dimension_offset', 15.0)
            if orientation == 'horizontal':
                # Place dimension below the line
                self._add_aligned_dimension(start, end, -offset_distance)
            else:
                # Place dimension to the left of the line
                self._add_aligned_dimension(start, end, -offset_distance)
            
            processed_lengths.add(length_key)
            dimension_count += 1
        
        return dimension_count
    
    def _add_aligned_dimension(self, p1, p2, distance):
        """Adds an aligned dimension."""
        try:
            dim = self.msp.add_aligned_dim(
                p1=(p1.x, p1.y), 
                p2=(p2.x, p2.y), 
                distance=distance,
                dimstyle=self.style_name
            )
            dim.render()
            return dim
        except Exception as e:
            print(f"[WARNING] Could not create dimension: {e}")
            return None
    
    def _add_diameter_dimension(self, circle):
        """Adds a diameter dimension, avoiding duplicates."""
        try:
            center = Vec2(circle.dxf.center)
            diameter = 2 * circle.dxf.radius
            rounded_dia = round(diameter, 1)

            for existing_dia in self.dimensioned_diameters:
                if abs(existing_dia - rounded_dia) < 0.2:
                    return None

            self.dimensioned_diameters.add(rounded_dia)

            dim = self.msp.add_diameter_dim(
                center=(center.x, center.y),
                radius=circle.dxf.radius,
                angle=45,
                dimstyle=self.style_name
            )   
            dim.render()
            return dim
        except Exception as e:
            print(f"[WARNING] Could not create diameter dimension: {e}")
            return None


    
    def _add_radius_dimension(self, arc):
     """Adds a radius dimension, avoiding duplicates by radius value."""
     try:
        center = Vec2(arc.dxf.center)
        radius = arc.dxf.radius
        rounded_radius = round(radius, 1)

        for existing_radius in self.dimensioned_radii:
            if abs(existing_radius - rounded_radius) < 0.2:
                return None  # Duplicate radius already dimensioned

        self.dimensioned_radii.add(rounded_radius)

        angle = (arc.dxf.start_angle + arc.dxf.end_angle) / 2
        dim = self.msp.add_radius_dim(
            center=(center.x, center.y),
            radius=radius,
            angle=angle,
            dimstyle=self.style_name
        )
        dim.render()
        return dim
     except Exception as e:
        print(f"[WARNING] Could not create radius dimension: {e}")
        return None

    
    def _dimension_angles(self, lines):
     """Dimensions important angles, avoiding duplicates."""
     if len(lines) < 2:
        return 0

     angle_count = 0
     max_angles = 5
     seen_angles = set()

     for i in range(min(len(lines), max_angles)):
        for j in range(i + 1, min(len(lines), max_angles)):
            line1, line2 = lines[i], lines[j]
            intersection = self._find_line_intersection(line1, line2)
            if intersection:
                angle = self._calculate_angle_between_lines(line1, line2)
                rounded = round(angle, 1)
                if 10 < angle < 170 and rounded not in seen_angles:
                    if self._add_angular_dimension(line1, line2, intersection):
                        seen_angles.add(rounded)
                        angle_count += 1

     return angle_count

    
    def _find_line_intersection(self, line1, line2):
        """Finds the intersection point of two lines."""
        p1 = Vec2(line1.dxf.start)
        p2 = Vec2(line1.dxf.end)
        p3 = Vec2(line2.dxf.start)
        p4 = Vec2(line2.dxf.end)
        
        # Direction vectors for each line
        d1 = p2 - p1
        d2 = p4 - p3
        
        # Check for parallelism
        det = d1.x * d2.y - d1.y * d2.x
        if abs(det) < self.tolerance:
            return None  # Lines are parallel
        
        # Calculate intersection parameters
        dp = p3 - p1
        t1 = (dp.x * d2.y - dp.y * d2.x) / det
        t2 = (dp.x * d1.y - dp.y * d1.x) / det
        
        # Check if intersection lies on both segments
        if 0 <= t1 <= 1 and 0 <= t2 <= 1:
            return p1 + d1 * t1
        
        # Check if intersection is near endpoints (within extended tolerance)
        extended_tolerance = 5.0  # mm
        if -extended_tolerance <= t1 * d1.magnitude <= d1.magnitude + extended_tolerance and \
           -extended_tolerance <= t2 * d2.magnitude <= d2.magnitude + extended_tolerance:
            return p1 + d1 * t1
            
        return None
    
    def _calculate_angle_between_lines(self, line1, line2):
        """Calculates the angle between two lines in degrees."""
        # Direction vectors for each line
        d1 = Vec2(line1.dxf.end) - Vec2(line1.dxf.start)
        d2 = Vec2(line2.dxf.end) - Vec2(line2.dxf.start)
        
        # Normalize vectors
        d1_norm = d1.normalize()
        d2_norm = d2.normalize()
        
        # Calculate dot product
        dot_product = d1_norm.dot(d2_norm)
        
        # Clamp to avoid floating point errors
        dot_product = max(-1.0, min(1.0, dot_product))
        
        # Calculate angle (radians -> degrees)
        angle_rad = math.acos(abs(dot_product))
        angle_deg = math.degrees(angle_rad)
        
        return min(angle_deg, 180 - angle_deg)  # Return the smaller angle
    
    def _add_angular_dimension(self, line1, line2, vertex):
     """Adds an angular dimension, compatible with ezdxf 0.18 and 0.20."""
     try:
        p1_start, p1_end = Vec2(line1.dxf.start), Vec2(line1.dxf.end)
        p2_start, p2_end = Vec2(line2.dxf.start), Vec2(line2.dxf.end)

        # Choose the point furthest from the vertex on each line
        point1 = p1_end if (vertex - p1_end).magnitude > (vertex - p1_start).magnitude else p1_start
        point2 = p2_end if (vertex - p2_end).magnitude > (vertex - p2_start).magnitude else p2_start

        # ✅ Prioritize 'center' first (newer), fallback to 'base' if error
        try:
            dim = self.msp.add_angular_dim_3p(
                center=(vertex.x, vertex.y),
                p1=(point1.x, point1.y),
                p2=(point2.x, point2.y),
                dimstyle=self.style_name
            )
        except TypeError:
            dim = self.msp.add_angular_dim_3p(
                base=(vertex.x, vertex.y),
                p1=(point1.x, point1.y),
                p2=(point2.x, point2.y),
                dimstyle=self.style_name
            )

        dim.render()
        return dim

     except Exception as e:
        print(f"[WARNING] Could not create angular dimension: {e}")
        return None


class AutoScaler:
    """Automatically adjusts scale based on paper size."""
    
    PAPER_SIZES = {
        'A0': (841, 1189),
        'A1': (594, 841),
        'A2': (420, 594),
        'A3': (297, 420),
        'A4': (210, 297),
        'A5': (148, 210)
    }
    
    @staticmethod
    def calculate_optimal_scale(geometry_bounds, paper_size, margin_ratio=0.1):
        """Calculates the optimal scale to fit geometry onto a paper size."""
        if paper_size not in AutoScaler.PAPER_SIZES:
            return 1.0
        
        paper_width, paper_height = AutoScaler.PAPER_SIZES[paper_size]
        
        # Calculate usable area (minus margins)
        usable_width = paper_width * (1 - 2 * margin_ratio)
        usable_height = paper_height * (1 - 2 * margin_ratio)
        
        # Calculate required scale
        geometry_width, geometry_height = geometry_bounds
        
        scale_x = usable_width / geometry_width if geometry_width > 0 else 1.0
        scale_y = usable_height / geometry_height if geometry_height > 0 else 1.0
        
        # Choose the smaller scale to ensure full fit
        optimal_scale = min(scale_x, scale_y)
        
        # Round down to the nearest standard scale
        standard_scales = [0.1, 0.2, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
        for scale in reversed(standard_scales):
            if optimal_scale >= scale:
                return scale
        
        return 0.1  # Smallest scale

def main():
    """Main function with enhanced dimensioning."""
    print("=== Enhanced DXF Dimensioning System ===")
    
    INPUT_DXF = "/app/output/step1_from_freecad.dxf"
    OUTPUT_DXF = "/app/output/step2_with_dims.dxf"
    CONFIG_PATH = "/app/config.json"
    
    try:
        # Load configuration
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        
        # Dimension configuration
        dimension_config = {
            'dimension_offset': float(config.get('DIMENSION_OFFSET', '15.0')),
            'text_height': float(config.get('DIMENSION_TEXT_HEIGHT', '2.5')),
            'min_dimension_length': float(config.get('MIN_DIMENSION_LENGTH', '5.0')),
            'max_dimensions_per_view': int(config.get('MAX_DIMENSIONS_PER_VIEW', '20')),
            'dimension_angles': config.get('DIMENSION_ANGLES', 'true').lower() == 'true',
            'dimension_radii': config.get('DIMENSION_RADII', 'true').lower() == 'true',
            'dimension_diameters': config.get('DIMENSION_DIAMETERS', 'true').lower() == 'true',
            'standard': config.get('DRAWING_STANDARD', 'ISO')
        }
        
        print(f"[INFO] Using standard: {dimension_config['standard']}")
        
        # Read DXF file
        doc = ezdxf.readfile(INPUT_DXF)
        msp = doc.modelspace()
        
        # Get all entities
        all_entities = list(msp.query("LINE CIRCLE ARC"))
        print(f"[INFO] Found {len(all_entities)} geometric entities.")
        
        if not all_entities:
            print("[WARNING] No entities found to dimension.")
            return
        
        # Classify by projection
        classifier = GeometryClassifier()
        projections = classifier.classify_by_projection(all_entities)
        
        for proj_name, entities in projections.items():
            print(f"[INFO] Classified {len(entities)} entities in {proj_name.upper()} view.")
        
        # Perform smart dimensioning
        dimensioner = SmartDimensioner(msp, dimension_config, dimension_config['standard'])
        total_dimensions = dimensioner.dimension_projections(projections)
        
        # Save file
        doc.saveas(OUTPUT_DXF)
        
        print(f"✅ [SUCCESS] Added {total_dimensions} dimensions using {dimension_config['standard']} standard.")
        print(f"✅ Output file saved to: {OUTPUT_DXF}")
        
    except Exception as e:
        print(f"❌ [ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
