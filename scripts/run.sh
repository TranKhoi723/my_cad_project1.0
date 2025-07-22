#!/bin/bash
# scripts/run.sh

# --- Thiết lập đường dẫn ---
PROJECT_ROOT=$(dirname "$(realpath "$0")")/..
INPUT_DIR="$PROJECT_ROOT/input"
TEMPLATE_DIR="$PROJECT_ROOT/templates"
OUTPUT_DIR="$PROJECT_ROOT/output"
SCRIPT_DIR="$PROJECT_ROOT/scripts"
CONFIG_FILE="$PROJECT_ROOT/config.tmp.json" # File cấu hình tạm thời

# --- Dọn dẹp ---
echo "🧹 Dọn dẹp các file output và config cũ..."
rm -f "$OUTPUT_DIR"/*
rm -f "$CONFIG_FILE"
echo ""

# --- BƯỚC 1: CHỌN FILE STEP ---
echo " STEP 1: Chọn file STEP để xử lý"
echo "-------------------------------------"
mapfile -t step_files < <(ls -1 "$INPUT_DIR"/*.step 2>/dev/null)
if [ ${#step_files[@]} -eq 0 ]; then
    echo "❌ Lỗi: Không tìm thấy file .step nào trong thư mục ./input/"
    exit 1
fi
PS3="Nhập số tương ứng với file bạn muốn chọn: "
select selected_step_path in "${step_files[@]}"; do
    if [[ -n "$selected_step_path" ]]; then
        INPUT_FILE=$(basename "$selected_step_path")
        break
    else
        echo "Lựa chọn không hợp lệ."
    fi
done
echo ""

# --- BƯỚC 2: CHỌN TEMPLATE ---
echo " STEP 2: Chọn template (khung tên/khổ giấy)"
echo "------------------------------------------------"
mapfile -t template_files < <(ls -1 "$TEMPLATE_DIR"/*.svg 2>/dev/null)
if [ ${#template_files[@]} -eq 0 ]; then
    echo "❌ Lỗi: Không tìm thấy file template .svg nào trong thư mục ./templates/"
    exit 1
fi
PS3="Nhập số tương ứng với template bạn muốn dùng: "
select selected_template_path in "${template_files[@]}"; do
    if [[ -n "$selected_template_path" ]]; then
        TEMPLATE_FILE=$(basename "$selected_template_path")
        PAPER_SIZE=$(basename "$TEMPLATE_FILE" .svg | sed 's/template_//' | tr '[:lower:]' '[:upper:]')
        break
    else
        echo "Lựa chọn không hợp lệ."
    fi
done
echo ""

# --- BƯỚC 3: CẤU HÌNH THÔNG SỐ BẢN VẼ ---
echo " STEP 3: Cấu hình thông số bản vẽ"
echo "-------------------------------------"
read -p "Nhập tỉ lệ (ví dụ: 0.1) [Mặc định: 1]: " SCALE_INPUT
SCALE=${SCALE_INPUT:-1}

read -p "Chọn kiểu chiếu (THIRD_ANGLE/FIRST_ANGLE) [Mặc định: THIRD_ANGLE]: " PROJ_METHOD_INPUT
PROJECTION_METHOD=${PROJ_METHOD_INPUT:-THIRD_ANGLE}

read -p "Nhập hệ số khoảng cách giữa các hình chiếu (ví dụ: 1.5) [Mặc định: 1.5]: " SPACING_FACTOR_INPUT
SPACING_FACTOR=${SPACING_FACTOR_INPUT:-1.5}

read -p "Nhập khoảng cách tối thiểu giữa các hình chiếu (mm) [Mặc định: 20.0]: " MIN_SPACING_INPUT
MIN_SPACING=${MIN_SPACING_INPUT:-20.0}

read -p "Nhập khoảng cách đường kích thước so với hình chiếu (mm) [Mặc định: 15.0]: " DIM_OFFSET_INPUT
DIMENSION_OFFSET=${DIM_OFFSET_INPUT:-15.0}

read -p "Nhập chiều cao chữ kích thước (mm) [Mặc định: 2.5]: " DIM_TEXT_HEIGHT_INPUT
DIMENSION_TEXT_HEIGHT=${DIM_TEXT_HEIGHT_INPUT:-2.5}

read -p "Nhập chiều dài tối thiểu của kích thước cần tự động tạo (mm) [Mặc định: 5.0]: " MIN_DIM_LEN_INPUT
MIN_DIMENSION_LENGTH=${MIN_DIM_LEN_INPUT:-5.0}

read -p "Nhập số lượng kích thước tối đa mỗi hình chiếu [Mặc định: 20]: " MAX_DIMS_INPUT
MAX_DIMENSIONS_PER_VIEW=${MAX_DIMS_INPUT:-20}

read -p "Tự động ghi kích thước góc (true/false) [Mặc định: true]: " DIM_ANGLES_INPUT
DIMENSION_ANGLES=${DIM_ANGLES_INPUT:-true}

read -p "Tự động ghi kích thước bán kính (true/false) [Mặc định: true]: " DIM_RADII_INPUT
DIMENSION_RADII=${DIM_RADII_INPUT:-true}

read -p "Tự động ghi kích thước đường kính (true/false) [Mặc định: true]: " DIM_DIAMETERS_INPUT
DIMENSION_DIAMETERS=${DIM_DIAMETERS_INPUT:-true}
echo ""

# --- XÁC NHẬN ---
echo "================ TÓM TẮT CẤU HÌNH ================"
echo "  File vào             : $INPUT_FILE"
echo "  Template             : $TEMPLATE_FILE (Khổ giấy: $PAPER_SIZE)"
echo "  Tỉ lệ                : $SCALE"
echo "  Kiểu chiếu           : $PROJECTION_METHOD"
echo "  Hệ số khoảng cách    : $SPACING_FACTOR"
echo "  Khoảng cách tối thiểu: $MIN_SPACING mm"
echo "  Offset đường kích thước: $DIMENSION_OFFSET mm"
echo "  Chiều cao chữ kích thước: $DIMENSION_TEXT_HEIGHT mm"
echo "  Chiều dài dim tối thiểu: $MIN_DIMENSION_LENGTH mm"
echo "  Dim tối đa/hình chiếu: $MAX_DIMENSIONS_PER_VIEW"
echo "  Ghi kích thước góc   : $DIMENSION_ANGLES"
echo "  Ghi kích thước bán kính: $DIMENSION_RADII"
echo "  Ghi kích thước đường kính: $DIMENSION_DIAMETERS"
echo "================================================="
read -p "Bạn có muốn tiếp tục? (Y/n): " confirm
if [[ "$confirm" != "Y" && "$confirm" != "y" && "$confirm" != "" ]]; then
    echo "Hủy bỏ."
    exit 0
fi

# --- TẠO FILE CẤU HÌNH ---
echo "📝 Tạo file cấu hình tạm thời..."
cat > "$CONFIG_FILE" << EOL
{
  "INPUT_FILE": "$INPUT_FILE",
  "TEMPLATE_FILE": "$TEMPLATE_FILE",
  "PROJECTION_METHOD": "$PROJECTION_METHOD",
  "SPACING_FACTOR": "$SPACING_FACTOR",
  "MIN_SPACING": "$MIN_SPACING",
  "DIMENSION_OFFSET": "$DIMENSION_OFFSET",
  "DIMENSION_TEXT_HEIGHT": "$DIMENSION_TEXT_HEIGHT",
  "MIN_DIMENSION_LENGTH": "$MIN_DIMENSION_LENGTH",
  "MAX_DIMENSIONS_PER_VIEW": "$MAX_DIMENSIONS_PER_VIEW",
  "DIMENSION_ANGLES": "$DIMENSION_ANGLES",
  "DIMENSION_RADII": "$DIMENSION_RADII",
  "DIMENSION_DIAMETERS": "$DIMENSION_DIAMETERS"
}
EOL
echo "✅ Đã tạo file config.tmp.json"
echo ""

# --- THỰC THI BẰNG DOCKER ---
echo "🐳 Đang build Docker image (nếu cần)..."
# Đã bỏ cờ --no-cache để các lần sau build nhanh hơn
docker build -t freecad-automation-macro "$PROJECT_ROOT" > /dev/null

echo "🚀 Bắt đầu quy trình xử lý bên trong container..."
docker run --rm \
  -v "$INPUT_DIR:/app/input" \
  -v "$TEMPLATE_DIR:/app/templates" \
  -v "$OUTPUT_DIR:/app/output" \
  -v "$SCRIPT_DIR:/app/scripts" \
  -v "$CONFIG_FILE:/app/config.json" \
  freecad-automation-macro

# Dọn dẹp file config sau khi chạy xong
rm -f "$CONFIG_FILE"

echo "🎉🎉🎉 QUY TRÌNH HOÀN TẤT! 🎉🎉🎉"
final_svg_file="$OUTPUT_DIR/final_drawing.svg"
if [[ -f "$final_svg_file" ]]; then
    echo "👀 Mở file kết quả: $final_svg_file"
    command -v xdg-open > /dev/null && xdg-open "$final_svg_file" || echo "Không thể tự động mở file."
else
    echo "❌ Lỗi: Không tìm thấy file output cuối cùng 'final_drawing.svg'."
fi