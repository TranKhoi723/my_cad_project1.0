#!/usr/bin/env python3
# scripts/pipeline.py

import os, subprocess, sys, json

def run_command(command):
    print(f"--- Đang chạy lệnh: {' '.join(command)} ---")
    subprocess.run(command, check=True)

def main():
    print("🚀 Bắt đầu quy trình pipeline...")
    with open("/app/config.json", 'r') as f: config = json.load(f)
    print("ℹ️ Cấu hình nhận được từ file config.json:")
    for key, value in config.items(): print(f"  {key}: {value}")
    template_path = f"/app/templates/{config['TEMPLATE_FILE']}"
    
    try:
        # Bước 1: FreeCAD (Draft) tạo bố cục DXF đã được chuẩn hóa
        run_command(["xvfb-run", "freecadcmd", "/app/scripts/freecad_techdraw_core.py"])
        
        # Bước 2: ezdxf thêm kích thước nâng cao
        run_command(["python", "/app/scripts/dxf_add_dim.py"])
        
        # Bước 3: Render SVG
        run_command(["python", "/app/scripts/dxf_render_svg.py", template_path])
        
        print("✅ Pipeline bên trong container hoàn tất thành công!")
    
    except Exception as e:
        print(f"❌ Một lỗi không mong muốn đã xảy ra: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()