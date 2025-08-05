import ezdxf
import os
# Import the entire math module of ezdxf for safe use
from ezdxf import math
from ezdxf.bbox import extents

def main():
    """
    Reads a DXF file, calculates the overall bounding box,
    and translates all entities so that the bottom-left corner is at the origin (0,0).
    This is a crucial "cleanup" step.
    """
    print("--- Starting dxf_normalizer.py script ---")
    
    input_path = "/app/output/step1_from_freecad.dxf"
    # The output of this script will be the input for the add_dim script
    output_path = "/app/output/step1_normalized.dxf" 

    try:
        doc = ezdxf.readfile(input_path)
        msp = doc.modelspace()
    except IOError:
        print(f"❌ ERROR: Could not read DXF file at: {input_path}. FreeCAD step might have failed.")
        sys.exit(1)

    if len(msp) == 0:
        print("[WARNING] Input DXF file is empty. Generating an empty normalized file.")
        doc.saveas(output_path)
        return

    # Calculate the bounding box of all entities
    try:
        bbox = extents(msp, fast=True)
    except Exception as e:
        print(f"[WARNING] Could not calculate bounding box: {e}. Skipping normalization.")
        doc.saveas(output_path)
        return

    if not bbox.has_data:
        print("[WARNING] Bounding box has no data. Skipping normalization.")
        doc.saveas(output_path)
        return

    # === MAIN LOGIC: CALCULATE AND TRANSLATE ===
    
    # Create translation vector to bring the bottom-left corner (extmin) to (0,0,0)
    # Using ezdxf.math.Vec3() is the safest way
    translation_vector = math.Vec3(-bbox.extmin.x, -bbox.extmin.y, -bbox.extmin.z)
    
    print(f"[INFO] Original bounding box (min): ({bbox.extmin.x:.2f}, {bbox.extmin.y:.2f})")
    print(f"[INFO] Calculated translation vector: ({translation_vector.x:.2f}, {translation_vector.y:.2f})")
    
    # Translate all entities in modelspace
    for entity in msp:
        try:
            entity.translate(translation_vector.x, translation_vector.y, translation_vector.z)
        except AttributeError:
            # Skip entities that do not support translation (rare)
            print(f"[DEBUG] Skipping untranslatable entity: {entity.dxftype()}")
            continue

    doc.saveas(output_path)
    print(f"✅ [SUCCESS] File normalized and saved to: {output_path}")

if __name__ == "__main__":
    import sys
    try:
        main()
    except Exception as e:
        print(f"❌ An unexpected error occurred in dxf_normalizer.py: {e}")
        sys.exit(1)
