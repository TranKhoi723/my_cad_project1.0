import sys
import os
import time
import math

try:
    import FreeCAD as App
    import Part
    import TechDraw
    from FreeCAD import Vector, Units, Rotation
except Exception as e:
    sys.stderr.write(f"[ERROR] Could not import FreeCAD modules: {e}\n")
    sys.exit(1)

step_file_path = os.environ.get('FREECAD_STEP_FILE')
intermediate_fcstd_path = os.environ.get('FREECAD_OUTPUT_PATH')
template_path = os.environ.get('FREECAD_TEMPLATE_FILE')
scale_value = float(os.environ.get('FREECAD_SCALE', '1.0'))

if not step_file_path or not intermediate_fcstd_path or not template_path:
    sys.stderr.write("[ERROR] Missing required environment variables.\n")
    sys.exit(1)

def project_point(point: Vector, view_direction: Vector) -> Vector:
    view_direction = view_direction.normalize()
    z_axis = Vector(0, 0, 1)
    rot = Rotation()
    if not view_direction.isEqual(z_axis, 1e-6):
        if view_direction.isEqual(-z_axis, 1e-6):
            rot = Rotation(Vector(0, 1, 0), 180)
        else:
            axis = z_axis.cross(view_direction).normalize()
            angle = math.degrees(math.acos(z_axis.dot(view_direction)))
            rot = Rotation(axis, angle)
    return rot.multVec(point)

def find_furthest_projected_points(obj, direction: Vector):
    vertices = [v.Point for v in obj.Shape.Vertexes]
    projected = [(project_point(v, direction), v) for v in vertices]
    max_dist = 0
    p1 = p2 = None
    for i in range(len(projected)):
        for j in range(i + 1, len(projected)):
            d = (projected[i][0].sub(projected[j][0])).Length
            if d > max_dist:
                max_dist = d
                p1, p2 = projected[i][1], projected[j][1]
    return p1, p2

def estimate_bounds(obj, direction, scale):
    projected = [project_point(v.Point, direction) for v in obj.Shape.Vertexes]
    min_x = min(v.x for v in projected)
    max_x = max(v.x for v in projected)
    min_y = min(v.y for v in projected)
    max_y = max(v.y for v in projected)
    return (max_x - min_x) * scale, (max_y - min_y) * scale

def add_extent_dim(doc, page, view, obj, direction: Vector, axis: int):
    try:
        v1, v2 = find_furthest_projected_points(obj, direction)
        if not v1 or not v2:
            return
        dim = TechDraw.makeExtentDim(view, [v1, v2], axis)
        page.addView(dim)
        dim.FormatSpec = '%.1f mm'
    except Exception as e:
        sys.stderr.write(f"[WARN] Could not create extent dim: {e}\n")

def add_radius_dims_from_edges(doc, page, view):
    count = 0
    try:
        for i, edge in enumerate(view.Source[0].Shape.Edges):
            if hasattr(edge.Curve, "Radius"):
                ref = [(view, f"Edge{i+1}")]
                try:
                    dim = TechDraw.makeRadiusDim(ref)
                    page.addView(dim)
                    dim.FormatSpec = '%.1f mm'
                    count += 1
                except Exception as e:
                    sys.stderr.write(f"[ERROR] Radius dim failed on Edge{i+1}: {e}\n")
    except Exception as e:
        sys.stderr.write(f"[WARN] Could not create radius dim: {e}\n")
    print(f"[INFO] Radius dimensions added: {count}")

doc = App.newDocument("DrawingDocument")
Part.insert(step_file_path, doc.Name)
doc.recompute()
part = doc.Objects[0]

page = doc.addObject("TechDraw::DrawPage", "Page")
template = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
template.Template = template_path
page.Template = template

views = {}
directions = {
    "Front": Vector(0, -1, 0),
    "Top": Vector(0, 0, 1),
    "Right": Vector(-1, 0, 0),
    "Iso": Vector(1, 1, 1).normalize()
}

for name, dir_vec in directions.items():
    view = doc.addObject("TechDraw::DrawViewPart", f"{name}View")
    view.Source = [part]
    view.Direction = dir_vec
    view.ScaleType = "Custom"
    view.Scale = scale_value
    page.addView(view)
    views[name] = view

doc.recompute()
time.sleep(1)

# Layout views
page_width = page.PageWidth
page_height = page.PageHeight
dims_est = {}
for k in directions:
    w, h = estimate_bounds(part, directions[k], scale_value)
    dims_est[k] = {"width": w, "height": h}

margin = 30
spacing = 50

views["Iso"].X = Units.Quantity(page_width - margin - dims_est["Iso"]["width"] / 2, "mm")
views["Iso"].Y = Units.Quantity(page_height - margin - dims_est["Iso"]["height"] / 2, "mm")

block_w = dims_est["Front"]["width"] + spacing + dims_est["Right"]["width"]
block_h = dims_est["Front"]["height"] + spacing + dims_est["Top"]["height"]
block_x = (page_width - block_w) / 2
block_y = (page_height - block_h) / 2

views["Front"].X = Units.Quantity(block_x + dims_est["Front"]["width"] / 2, "mm")
views["Front"].Y = Units.Quantity(block_y + dims_est["Front"]["height"] / 2, "mm")

views["Top"].X = views["Front"].X
views["Top"].Y = Units.Quantity(views["Front"].Y.Value + dims_est["Front"]["height"] / 2 + spacing + dims_est["Top"]["height"] / 2, "mm")

views["Right"].X = Units.Quantity(views["Front"].X.Value + dims_est["Front"]["width"] / 2 + spacing + dims_est["Right"]["width"] / 2, "mm")
views["Right"].Y = views["Front"].Y

doc.recompute()
time.sleep(1)

# Final dimensioning
for name in ["Front", "Top", "Right"]:
    add_extent_dim(doc, page, views[name], part, directions[name], 0)
    add_extent_dim(doc, page, views[name], part, directions[name], 1)
    add_radius_dims_from_edges(doc, page, views[name])

doc.recompute()
output_path = os.path.splitext(intermediate_fcstd_path)[0] + ".FCStd"
doc.saveAs(output_path)
print(f"[INFO] FCStd saved to: {output_path}")
App.closeDocument(doc.Name)
sys.exit(0)
