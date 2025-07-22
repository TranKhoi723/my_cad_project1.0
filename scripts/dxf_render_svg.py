# scripts/dxf_render_svg.py
import os, sys, re
import ezdxf
from lxml import etree
import matplotlib.pyplot as plt
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, ColorPolicy
from ezdxf.bbox import extents
from io import BytesIO

def main():
    """
    Kết hợp bản vẽ và template bằng phương pháp Hybrid Vector Merge.
    Học hỏi từ mã nguồn của người dùng:
    - Sử dụng viewBox của template để xác định khổ giấy.
    - Dùng transform với scale âm ở trục Y để lật hệ tọa độ.
    - Ghép trực tiếp các vector để giữ độ sắc nét.
    """
    print("--- Bắt đầu dxf_render_svg.py (Phiên bản Hybrid Vector Merge) ---")

    if len(sys.argv) < 2:
        sys.exit("LỖI: Thiếu đường dẫn file template.")
    
    template_path = sys.argv[1]
    dxf_file_to_read = "/app/output/step2_with_dims.dxf"
    final_svg_output_path = "/app/output/final_drawing.svg"

    # --- BƯỚC A: DÙNG MATPLOTLIB ĐỂ RENDER DXF RA CHUỖI SVG TRONG BỘ NHỚ ---
    try:
        doc = ezdxf.readfile(dxf_file_to_read)
        msp = doc.modelspace()
        if not msp or len(msp) == 0:
            print("[CẢNH BÁO] Modelspace trống. Sẽ tạo ra bản vẽ rỗng.")
            bbox = None
        else:
            bbox = extents(msp, fast=True)
    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file DXF đầu vào tại '{dxf_file_to_read}'.")
        sys.exit(1)
    except Exception as e:
        print(f"LỖI khi đọc file DXF: {e}")
        sys.exit(1)

    print("[INFO] Bắt đầu render hình chiếu bằng Matplotlib...")
    fig, ax = plt.subplots()
    config = Configuration.defaults().with_changes(color_policy=ColorPolicy.BLACK)
    backend = MatplotlibBackend(ax)
    from ezdxf.addons.drawing import Frontend, RenderContext
    Frontend(RenderContext(doc), backend, config=config).draw_layout(msp)
    backend.finalize()

    # Lưu vào buffer trong bộ nhớ thay vì file tạm
    drawing_buffer = BytesIO()
    fig.savefig(drawing_buffer, format='svg', transparent=True)
    plt.close(fig)
    drawing_buffer.seek(0)
    drawing_svg_string = drawing_buffer.read()

    # --- BƯỚC B: GHÉP CÁC VECTOR VÀO TEMPLATE BẰNG LXML ---
    print("[INFO] Bắt đầu ghép vector vào template...")
    try:
        parser = etree.XMLParser(remove_blank_text=True)
        template_tree = etree.parse(template_path, parser)
        template_root = template_tree.getroot()
        drawing_root = etree.fromstring(drawing_svg_string)

        # Lấy kích thước khổ giấy từ viewBox của template
        t_vb_str = template_root.get('viewBox', '0 0 420 297')
        t_vb = [float(f) for f in t_vb_str.split()]
        t_width, t_height = t_vb[2], t_vb[3]
        
        # Tạo một group rỗng để chứa bản vẽ
        final_drawing_group = etree.Element("g", id="FinalDrawing")

        if bbox and bbox.has_data:
            d_min, d_max = bbox.extmin, bbox.extmax
            d_width = d_max.x - d_min.x if d_max.x > d_min.x else 1
            d_height = d_max.y - d_min.y if d_max.y > d_min.y else 1

            # Tính toán scale và translate để căn giữa và vừa vặn
            margin = 0.05 # 5% lề
            target_w = t_width * (1 - 2 * margin)
            target_h = t_height * (1 - 2 * margin)
            
            scale = min(target_w / d_width, target_h / d_height)
            scaled_w = d_width * scale
            scaled_h = d_height * scale

            # Logic dịch chuyển để căn giữa
            translate_x = (t_width - scaled_w) / 2 - (d_min.x * scale)
            # Logic dịch chuyển và lật trục Y
            translate_y = (t_height + scaled_h) / 2 + (d_min.y * scale)
            
            transform_str = f"translate({translate_x:.3f}, {translate_y:.3f}) scale({scale:.4f}, {-scale:.4f})"
            final_drawing_group.set('transform', transform_str)
            print(f"[INFO] Áp dụng transform: {transform_str}")

        # Tìm group chính chứa các nét vẽ từ Matplotlib
        NS = {'svg': 'http://www.w3.org/2000/svg'}
        main_figure_group = drawing_root.find('svg:g', namespaces=NS)
        if main_figure_group is not None:
            # Sao chép tất cả các phần tử con (paths, etc.) vào group mới của chúng ta
            for element in main_figure_group:
                final_drawing_group.append(element)
        else:
            print("[CẢNH BÁO] Không tìm thấy group hình học trong SVG từ Matplotlib.")

        template_root.append(final_drawing_group)
        template_tree.write(final_svg_output_path, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        print(f"✅ [THÀNH CÔNG] Đã tạo file SVG hoàn chỉnh tại: {final_svg_output_path}")

    except Exception as e:
        print(f"LỖI trong Bước B (Ghép SVG): {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()