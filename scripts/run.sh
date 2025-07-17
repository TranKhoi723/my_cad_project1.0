#!/bin/bash
set -e

PROJECT_ROOT=$(dirname "$(realpath "$0")")/..
INPUT_DIR="$PROJECT_ROOT/input"
TEMPLATE_DIR="$PROJECT_ROOT/templates"
OUTPUT_DIR="$PROJECT_ROOT/output"
SCRIPT_DIR="$PROJECT_ROOT/scripts"

SCALE="1.0"  # bạn có thể chỉnh tại đây nếu cần

# --- Tìm file STEP ---
STEP_FILES=("$INPUT_DIR"/*.step)

if [ ${#STEP_FILES[@]} -eq 0 ]; then
  echo "❌ Không tìm thấy file STEP trong thư mục: $INPUT_DIR"
  exit 1
elif [ ${#STEP_FILES[@]} -gt 1 ]; then
  echo "⚠️ Có nhiều file STEP, đang chọn file đầu tiên:"
  for file in "${STEP_FILES[@]}"; do echo "  - $(basename "$file")"; done
fi

INPUT_FILE=$(basename "${STEP_FILES[0]}")
TEMPLATE_FILE="template_a4.svg"
OUTPUT_BASE="${INPUT_FILE%.*}"

mkdir -p "$OUTPUT_DIR"
docker build -t freecad-automation-macro "$PROJECT_ROOT"

# --- Bước 1: FreeCAD pipeline ---
docker run --rm \
  -e INPUT_FILE_PATH="/app/input/$INPUT_FILE" \
  -e TEMPLATE_FILE_PATH="/app/templates/$TEMPLATE_FILE" \
  -e OUTPUT_BASE="$OUTPUT_BASE" \
  -e FREECAD_SCALE="$SCALE" \
  -v "$INPUT_DIR:/app/input" \
  -v "$TEMPLATE_DIR:/app/templates" \
  -v "$OUTPUT_DIR:/app/output" \
  -v "$SCRIPT_DIR:/app/scripts" \
  freecad-automation-macro \
  freecadcmd /app/scripts/pipeline.py

# --- Bước 2: thêm DIM vào DXF ---
docker run --rm \
  -e OUTPUT_BASE="$OUTPUT_BASE" \
  -v "$OUTPUT_DIR:/app/output" \
  -v "$SCRIPT_DIR:/app/scripts" \
  freecad-automation-macro \
  python3 /app/scripts/dxf_add_dim.py

# --- Bước 3: render SVG (có khung) ---
docker run --rm \
  -e OUTPUT_BASE="$OUTPUT_BASE" \
  -v "$OUTPUT_DIR:/app/output" \
  -v "$TEMPLATE_DIR:/app/templates" \
  -v "$SCRIPT_DIR:/app/scripts" \
  freecad-automation-macro \
  python3 /app/scripts/dxf_render_svg.py
