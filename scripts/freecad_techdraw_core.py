# scripts/freecad_draft_core.py
import sys, os, json, traceback
import FreeCAD as App
import Part, Draft, importDXF
from FreeCAD import Vector

try:
    print("[INFO] freecad_draft_core.py: Bắt đầu xử lý...")

    with open("/app/config.json", 'r') as f:
        config = json.load(f)

    input_filename = config.get("INPUT_FILE")
    scale = float(config.get("SCALE", "1.0"))
    projection_method = config.get("PROJECTION_METHOD", "THIRD_ANGLE").upper()
    min_spacing = float(config.get("MIN_SPACING", "20.0"))

    if not input_filename:
        raise ValueError("Thiếu INPUT_FILE trong config.json.")

    step_file_path = os.path.join("/app/input", input_filename)
    output_dxf_path = "/app/output/step1_from_freecad.dxf"

    print(f"[INFO] File vào: {step_file_path}, Scale: {scale}, Projection: {projection_method}")
    
    doc = App.newDocument("Draft_Drawing")
    shape = Part.read(step_file_path) 
    part_obj = doc.addObject("Part::Feature", os.path.splitext(input_filename)[0])
    part_obj.Shape = shape
    doc.recompute()

    print("[INFO] Tạo các hình chiếu 2D...")
    views = {}
    directions = {
        "Front": Vector(0, -1, 0), "Top": Vector(0, 0, 1),
        "Right": Vector(1, 0, 0), "Isometric": Vector(1, 1, 1).normalize()
    }
    for name, direction in directions.items():
        view = Draft.makeShape2DView(part_obj, direction)
        view.Label = f"{name}View"
        views[name] = view
    doc.recompute()
    
    # === SỬA LỖI: ÁP DỤNG TỈ LỆ BẰNG Draft.scale() ===
    print("[INFO] Áp dụng tỉ lệ cho các hình chiếu...")
    scale_vector = Vector(scale, scale, scale)
    for view_obj in views.values():
        # Scale đối tượng quanh tâm của nó
        Draft.scale(view_obj, scale_vector, center=view_obj.Shape.BoundBox.Center, copy=False)
    doc.recompute()

    print("[INFO] Sắp xếp vị trí các hình chiếu...")
    bbox_front = views["Front"].Shape.BoundBox
    bbox_top = views["Top"].Shape.BoundBox
    bbox_right = views["Right"].Shape.BoundBox

    views["Front"].Placement.Base = Vector(0, 0, 0)
    doc.recompute()

    # Khoảng cách bây giờ không cần nhân với scale nữa vì các bbox đã được scale
    if projection_method == "THIRD_ANGLE":
        views["Top"].Placement.Base.x = (bbox_front.XLength / 2) - (bbox_top.XLength / 2)
        views["Top"].Placement.Base.y = bbox_front.YLength + min_spacing
        views["Right"].Placement.Base.x = bbox_front.XLength + min_spacing
        views["Right"].Placement.Base.y = (bbox_front.YLength / 2) - (bbox_right.YLength / 2)
    else: # FIRST_ANGLE
        views["Top"].Placement.Base.x = (bbox_front.XLength / 2) - (bbox_top.XLength / 2)
        views["Top"].Placement.Base.y = -min_spacing - bbox_top.YLength
        views["Right"].Placement.Base.x = -min_spacing - bbox_right.XLength
        views["Right"].Placement.Base.y = (bbox_front.YLength / 2) - (bbox_right.YLength / 2)
    doc.recompute()

    all_main_views = [views["Front"], views["Top"], views["Right"]]
    combined_bbox = App.BoundBox()
    for view in all_main_views:
        combined_bbox.add(view.Shape.BoundBox)
    views["Isometric"].Placement.Base.x = combined_bbox.XMax + min_spacing
    views["Isometric"].Placement.Base.y = combined_bbox.YMax - views["Isometric"].Shape.BoundBox.YLength
    doc.recompute()
    
    all_final_views = list(views.values())
    overall_bbox = App.BoundBox()
    for view in all_final_views:
        overall_bbox.add(view.Shape.BoundBox)

    translation_vector = Vector(-overall_bbox.XMin, -overall_bbox.YMin, 0)
    for view in all_final_views:
        view.Placement.Base = view.Placement.Base.add(translation_vector)
    doc.recompute()
    
    print(f"[INFO] Xuất ra file DXF: {output_dxf_path}")
    importDXF.export(all_final_views, output_dxf_path)
    
    print("✅ [THÀNH CÔNG] Đã xuất file DXF với bố cục đã được chuẩn hóa.")

except Exception as e:
    sys.stderr.write(f"\n❌ LỖI NGHIÊM TRỌNG trong freecad_draft_core.py: {e}\n")
    sys.stderr.write(traceback.format_exc())
    sys.exit(1)
finally:
    if 'doc' in locals() and doc is not None:
        try:
            App.closeDocument(doc.Name)
        except Exception: pass
    sys.exit(0)