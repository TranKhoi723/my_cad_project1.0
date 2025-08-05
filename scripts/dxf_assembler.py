import ezdxf, os, json, math
from ezdxf.math import Matrix44, X_AXIS, Y_AXIS
from ezdxf.addons import Importer
from ezdxf.bbox import extents

def main():
    print("--- Starting dxf_assembler.py script (Advanced Layout) ---")
    
    with open("/app/config.json", 'r') as f: config = json.load(f)
    min_spacing = float(config["MIN_SPACING"])
    template_file = config["TEMPLATE_FILE"]
    output_dir = "/app/output"
    
    final_dxf_path = os.path.join(output_dir, "step1_from_freecad.dxf")
    doc = ezdxf.new()
    msp = doc.modelspace()
    
    temp_files = {
        "TOP": os.path.join(output_dir, "temp_TOP.dxf"),
        "FRONT": os.path.join(output_dir, "temp_FRONT.dxf"),
        "RIGHT": os.path.join(output_dir, "temp_RIGHT.dxf"),
        "ISO": os.path.join(output_dir, "temp_ISO.dxf")
    }
    
    view_data = {}
    for name, filepath in temp_files.items():
        if not os.path.exists(filepath):
            print(f"[WARNING] Temporary file does not exist, skipping: {filepath}")
            continue
        source_doc = ezdxf.readfile(filepath)
        entities = list(source_doc.modelspace())
        if name == "FRONT":
            mat = Matrix44.axis_rotate(axis=X_AXIS, angle=math.radians(-90))
            for e in entities: e.transform(mat)
        elif name == "RIGHT":
            mat = Matrix44.axis_rotate(axis=Y_AXIS, angle=math.radians(90))
            for e in entities: e.transform(mat)
        bbox = extents(entities, fast=True)
        if bbox.has_data:
            mat_normalize = Matrix44.translate(-bbox.extmin.x, -bbox.extmin.y, -bbox.extmin.z)
            for e in entities: e.transform(mat_normalize)
        view_data[name] = {'entities': entities, 'bbox': extents(entities, fast=True)}

    # === FIX: CHECK FOR EXISTENCE OF REQUIRED PROJECTIONS ===
    if "FRONT" not in view_data or "TOP" not in view_data or "RIGHT" not in view_data:
        print("❌ ERROR: Missing one of the main projections (Front, Top, Right). Cannot arrange.")
        sys.exit(1)

    page_sizes = { "A0": (1189, 841), "A1": (841, 594), "A2": (594, 420), "A3": (420, 297), "A4": (297, 210) }
    page_key = template_file.split('_')[0].upper()
    page_width, page_height = page_sizes.get(page_key, (594, 420))

    dims = {name: (data['bbox'].size.x, data['bbox'].size.y) for name, data in view_data.items()}
    block_width = dims["FRONT"][0] + min_spacing + dims["RIGHT"][0]
    block_height = dims["TOP"][1] + min_spacing + dims["FRONT"][1]
    
    start_x = (page_width - block_width) / 2
    start_y = (page_height - block_height) / 2

    mat_front = Matrix44.translate(start_x, start_y, 0)
    mat_top = Matrix44.translate(start_x, start_y + dims["FRONT"][1] + min_spacing, 0)
    mat_right = Matrix44.translate(start_x + dims["FRONT"][0] + min_spacing, start_y, 0)
    
    # Apply transformation only if projection exists
    if "FRONT" in view_data:
        for e in view_data["FRONT"]['entities']: e.transform(mat_front)
    if "TOP" in view_data:
        for e in view_data["TOP"]['entities']: e.transform(mat_top)
    if "RIGHT" in view_data:
        for e in view_data["RIGHT"]['entities']: e.transform(mat_right)
    if "ISO" in view_data:
        mat_iso = Matrix44.translate(page_width - dims["ISO"][0] - 20, page_height - dims["ISO"][1] - 20, 0)
        for e in view_data["ISO"]['entities']: e.transform(mat_iso)

    for name, data in view_data.items():
        layer_name = f"VIEW_{name}"
        if layer_name not in doc.layers: doc.layers.new(name=layer_name)
        for entity in data['entities']:
            new_entity = entity.copy()
            new_entity.dxf.layer = layer_name
            msp.add_entity(new_entity)

    doc.saveas(final_dxf_path)
    print(f"✅ [SUCCESS] Views assembled into: {final_dxf_path}")
    
    for f in temp_files.values():
        if os.path.exists(f): os.remove(f)

if __name__ == "__main__":
    main()
