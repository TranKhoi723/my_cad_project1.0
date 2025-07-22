# scripts/dxf_normalizer.py
import ezdxf
import os
# Import toàn bộ module math của ezdxf để sử dụng một cách an toàn
from ezdxf import math
from ezdxf.bbox import extents

def main():
    """
    Đọc một file DXF, tính toán bounding box tổng thể,
    và dịch chuyển tất cả các thực thể để góc dưới-trái nằm ở gốc tọa độ (0,0).
    Đây là bước "dọn dẹp" cực kỳ quan trọng.
    """
    print("--- Bắt đầu script dxf_normalizer.py ---")
    
    input_path = "/app/output/step1_from_freecad.dxf"
    # Đầu ra của script này sẽ là đầu vào cho script add_dim
    output_path = "/app/output/step1_normalized.dxf" 

    try:
        doc = ezdxf.readfile(input_path)
        msp = doc.modelspace()
    except IOError:
        print(f"❌ LỖI: Không đọc được file DXF tại: {input_path}. Có thể bước FreeCAD đã thất bại.")
        sys.exit(1)

    if len(msp) == 0:
        print("[WARNING] File DXF đầu vào trống. Tạo ra file normalized rỗng.")
        doc.saveas(output_path)
        return

    # Tính toán bounding box của tất cả các thực thể
    try:
        bbox = extents(msp, fast=True)
    except Exception as e:
        print(f"[WARNING] Không thể tính toán bounding box: {e}. Bỏ qua việc chuẩn hóa.")
        doc.saveas(output_path)
        return

    if not bbox.has_data:
        print("[WARNING] Bounding box không có dữ liệu. Bỏ qua việc chuẩn hóa.")
        doc.saveas(output_path)
        return

    # === LOGIC CHÍNH: TÍNH TOÁN VÀ DỊCH CHUYỂN ===
    
    # Tạo vector dịch chuyển để đưa góc dưới-trái (extmin) về (0,0,0)
    # Sử dụng ezdxf.math.Vec3() là cách an toàn nhất
    translation_vector = math.Vec3(-bbox.extmin.x, -bbox.extmin.y, -bbox.extmin.z)
    
    print(f"[INFO] Bounding box gốc (min): ({bbox.extmin.x:.2f}, {bbox.extmin.y:.2f})")
    print(f"[INFO] Tính toán vector dịch chuyển: ({translation_vector.x:.2f}, {translation_vector.y:.2f})")
    
    # Dịch chuyển tất cả các thực thể trong modelspace
    for entity in msp:
        try:
            entity.translate(translation_vector.x, translation_vector.y, translation_vector.z)
        except AttributeError:
            # Bỏ qua các thực thể không hỗ trợ dịch chuyển (hiếm gặp)
            print(f"[DEBUG] Bỏ qua thực thể không thể dịch chuyển: {entity.dxftype()}")
            continue

    doc.saveas(output_path)
    print(f"✅ [THÀNH CÔNG] Đã chuẩn hóa và lưu file vào: {output_path}")

if __name__ == "__main__":
    import sys
    try:
        main()
    except Exception as e:
        print(f"❌ Một lỗi không mong muốn đã xảy ra trong dxf_normalizer.py: {e}")
        sys.exit(1)