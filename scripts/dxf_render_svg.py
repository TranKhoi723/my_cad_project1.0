# scripts/dxf_render_svg.py
# Hybrid Version - Final and precise Transform fix

import os
import sys
import traceback
from io import BytesIO

import ezdxf
from ezdxf.bbox import extents
from lxml import etree

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, ColorPolicy


def main():
    """
    Combines drawing and template, using the thoroughly fixed transform formula.
    """
    print("--- Starting dxf_render_svg.py (Hybrid Version - Final Transform fix) ---")

    if len(sys.argv) < 2:
        sys.exit("ERROR: Missing template file path.")
    
    template_path = sys.argv[1]
    dxf_file_to_read = "/app/output/step2_with_dims.dxf"
    final_svg_output_path = "/app/output/final_drawing.svg"

    # --- STEP A: Read DXF and get dimensions (width, height) ---
    try:
        doc = ezdxf.readfile(dxf_file_to_read)
        msp = doc.modelspace()
        bbox = extents(msp, fast=True) if msp and len(msp) > 0 else None
        if not bbox or not bbox.has_data:
            print("[WARNING] Modelspace is empty or BBox could not be calculated.")
            bbox = None

    except Exception as e:
        print(f"ERROR reading DXF file: {e}")
        sys.exit(1)

    # --- STEP B: Render DXF using Matplotlib (Unchanged) ---
    print("[INFO] Starting to render views using Matplotlib...")
    try:
        fig, ax = plt.subplots()
        config = Configuration.defaults().with_changes(color_policy=ColorPolicy.BLACK)
        backend = MatplotlibBackend(ax)
        Frontend(RenderContext(doc), backend, config=config).draw_layout(msp)
        
        ax.set_aspect('equal')
        ax.axis('off')
        fig.tight_layout(pad=0)

        drawing_buffer = BytesIO()
        fig.savefig(drawing_buffer, format='svg', transparent=True, bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
        drawing_buffer.seek(0)
        drawing_svg_string = drawing_buffer.read()
    except Exception as e:
        print(f"ERROR during Matplotlib rendering: {e}")
        traceback.print_exc()
        sys.exit(1)

    # --- STEP C: MERGE VECTOR INTO TEMPLATE WITH FIXED TRANSFORM ---
    print("[INFO] Starting to merge vector into template...")
    try:
        parser = etree.XMLParser(remove_blank_text=True, recover=True)
        template_tree = etree.parse(template_path, parser)
        template_root = template_tree.getroot()
        drawing_root = etree.fromstring(drawing_svg_string, parser=parser)

        t_vb_str = template_root.get('viewBox', '0 0 1189 841')
        t_vb = [float(f) for f in t_vb_str.split()]
        t_width, t_height = t_vb[2], t_vb[3]
        
        final_drawing_group = etree.Element("g", id="FinalDrawingContent")

        if bbox:
            d_width = bbox.size.x if bbox.size.x > 0 else 1.0
            d_height = bbox.size.y if bbox.size.y > 0 else 1.0

            margin = 0.05
            target_w = t_width * (1 - 2 * margin)
            target_h = t_height * (1 - 2 * margin)
            
            scale = min(target_w / d_width, target_h / d_height)
            scaled_w = d_width * scale
            scaled_h = d_height * scale

            # --- CORRECT TRANSFORM FORMULA ---
            # Assuming the drawing rendered by Matplotlib has been normalized to origin (0,0).
            # We just need to translate it to the center of the page.

            # Translate X to align the left edge of the drawing to the correct position
            translate_x = (t_width - scaled_w) / 2
            
            # Translate Y to align the top edge of the drawing (after flipping) to the correct position
            translate_y = (t_height - scaled_h) / 2
            # ---------------------------------
            
            transform_str = f"translate({translate_x:.4f}, {translate_y:.4f}) scale({scale:.5f}, {scale:.5f})"
            final_drawing_group.set('transform', transform_str)
            print(f"[INFO] Applying fixed transform: {transform_str}")

        NS = {'svg': 'http://www.w3.org/2000/svg'}
        main_figure_group = drawing_root.find('svg:g', namespaces=NS)
        if main_figure_group is not None:
            for element in main_figure_group:
                final_drawing_group.append(element)
        else:
            print("[WARNING] No geometry group found in SVG from Matplotlib.")

        template_root.append(final_drawing_group)
        template_tree.write(final_svg_output_path, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        print(f"✅ [SUCCESS] Generated complete SVG file at: {final_svg_output_path}")

    except Exception as e:
        print(f"ERROR in Step C (SVG Merging): {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
