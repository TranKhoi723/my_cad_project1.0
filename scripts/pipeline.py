import FreeCAD as App
import Part, Draft, importDXF
import os, json, sys

input_file = os.environ.get("INPUT_FILE_PATH")
template_path = os.environ.get("TEMPLATE_FILE_PATH")
output_base = os.environ.get("OUTPUT_BASE", "output")
scale = float(os.environ.get("FREECAD_SCALE", "1.0"))

dxf_path = f"/app/output/{output_base}.dxf"
dim_json_path = f"/app/output/{output_base}_coords.json"

doc = App.newDocument()
shape = Part.read(input_file)
part = doc.addObject("Part::Feature", "Part")
part.Shape = shape
doc.recompute()

view = Draft.makeShape2DView(part, App.Vector(0, -1, 0))
doc.recompute()

# Export DXF
importDXF.export([view], dxf_path)
print(f"DXF saved to: {dxf_path}")

# Bounding box for dimension
bbox = view.Shape.BoundBox
dim_data = {
    "dimensions": [
        {
            "type": "horizontal",
            "p1": [bbox.XMin, bbox.YMin],
            "p2": [bbox.XMax, bbox.YMin],
            "offset": -20
        }
    ]
}
with open(dim_json_path, 'w') as f:
    json.dump(dim_data, f)
print(f"Dimension data saved to: {dim_json_path}")

App.closeDocument(doc.Name)
