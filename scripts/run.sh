#!/bin/bash
# scripts/run.sh

# --- Setup Paths ---
PROJECT_ROOT=$(dirname "$(realpath "$0")")/..
INPUT_DIR="$PROJECT_ROOT/input"
TEMPLATE_DIR="$PROJECT_ROOT/templates"
OUTPUT_DIR="$PROJECT_ROOT/output"
SCRIPT_DIR="$PROJECT_ROOT/scripts"
CONFIG_FILE="$PROJECT_ROOT/config.tmp.json" # Temporary config file

# --- Cleanup ---
echo "🧹 Cleaning up old output files and configs..."
rm -f "$OUTPUT_DIR"/*
rm -f "$CONFIG_FILE"
echo ""

# --- STEP 1: SELECT STEP FILE ---
echo " STEP 1: Select STEP file to process"
echo "-------------------------------------"
mapfile -t step_files < <(ls -1 "$INPUT_DIR"/*.step 2>/dev/null)
if [ ${#step_files[@]} -eq 0 ]; then
    echo "❌ Error: No .step files found in the ./input/ directory"
    exit 1
fi
PS3="Enter the number for the file you want to select: "
select selected_step_path in "${step_files[@]}"; do
    if [[ -n "$selected_step_path" ]]; then
        INPUT_FILE=$(basename "$selected_step_path")
        break
    else
        echo "Invalid selection. Please try again."
    fi
done
echo ""

# --- STEP 2: SELECT TEMPLATE ---
echo " STEP 2: Select a template (title block/paper size)"
echo "------------------------------------------------"
mapfile -t template_files < <(ls -1 "$TEMPLATE_DIR"/*.svg 2>/dev/null)
if [ ${#template_files[@]} -eq 0 ]; then
    echo "❌ Error: No .svg template files found in the ./templates/ directory"
    exit 1
fi
PS3="Enter the number for the template you want to use: "
select selected_template_path in "${template_files[@]}"; do
    if [[ -n "$selected_template_path" ]]; then
        TEMPLATE_FILE=$(basename "$selected_template_path")
        PAPER_SIZE=$(basename "$TEMPLATE_FILE" .svg | sed 's/template_//' | tr '[:lower:]' '[:upper:]')
        break
    else
        echo "Invalid selection. Please try again."
    fi
done
echo ""

# --- STEP 3: CONFIGURE DRAWING PARAMETERS ---
echo " STEP 3: Configure drawing parameters"
echo "-------------------------------------"
read -p "Enter scale (e.g., 0.1) [Default: 1]: " SCALE_INPUT
SCALE=${SCALE_INPUT:-1}

read -p "Select projection method (THIRD_ANGLE/FIRST_ANGLE) [Default: THIRD_ANGLE]: " PROJ_METHOD_INPUT
PROJECTION_METHOD=${PROJ_METHOD_INPUT:-THIRD_ANGLE}

# This is the newly added section
read -p "Select drawing standard (ISO/ANSI) [Default: ISO]: " STANDARD_INPUT
DRAWING_STANDARD=${STANDARD_INPUT:-ISO}

read -p "Enter view spacing factor (e.g., 1.5) [Default: 1.5]: " SPACING_FACTOR_INPUT
SPACING_FACTOR=${SPACING_FACTOR_INPUT:-1.5}

read -p "Enter minimum view spacing (mm) [Default: 20.0]: " MIN_SPACING_INPUT
MIN_SPACING=${MIN_SPACING_INPUT:-20.0}

read -p "Enter dimension offset from view (mm) [Default: 15.0]: " DIM_OFFSET_INPUT
DIMENSION_OFFSET=${DIM_OFFSET_INPUT:-15.0}

read -p "Enter dimension text height (mm) [Default: 2.5]: " DIM_TEXT_HEIGHT_INPUT
DIMENSION_TEXT_HEIGHT=${DIM_TEXT_HEIGHT_INPUT:-2.5}

read -p "Enter minimum length for auto-dimensioning (mm) [Default: 5.0]: " MIN_DIM_LEN_INPUT
MIN_DIMENSION_LENGTH=${MIN_DIM_LEN_INPUT:-5.0}

read -p "Enter max dimensions per view [Default: 20]: " MAX_DIMS_INPUT
MAX_DIMENSIONS_PER_VIEW=${MAX_DIMS_INPUT:-20}

read -p "Automatically dimension angles (true/false) [Default: true]: " DIM_ANGLES_INPUT
DIMENSION_ANGLES=${DIM_ANGLES_INPUT:-true}

read -p "Automatically dimension radii (true/false) [Default: true]: " DIM_RADII_INPUT
DIMENSION_RADII=${DIM_RADII_INPUT:-true}

read -p "Automatically dimension diameters (true/false) [Default: true]: " DIM_DIAMETERS_INPUT
DIMENSION_DIAMETERS=${DIM_DIAMETERS_INPUT:-true}
echo ""

# --- CONFIRMATION ---
echo "================ CONFIGURATION SUMMARY ================"
echo "  Input File           : $INPUT_FILE"
echo "  Template             : $TEMPLATE_FILE (Paper Size: $PAPER_SIZE)"
echo "  Scale                : $SCALE"
echo "  Projection Method    : $PROJECTION_METHOD"
echo "  Drawing Standard     : $DRAWING_STANDARD"
echo "  Spacing Factor       : $SPACING_FACTOR"
echo "  Minimum Spacing      : $MIN_SPACING mm"
echo "  Dimension Offset     : $DIMENSION_OFFSET mm"
echo "  Dimension Text Height: $DIMENSION_TEXT_HEIGHT mm"
echo "  Min Dimension Length : $MIN_DIMENSION_LENGTH mm"
echo "  Max Dims Per View    : $MAX_DIMENSIONS_PER_VIEW"
echo "  Dimension Angles     : $DIMENSION_ANGLES"
echo "  Dimension Radii      : $DIMENSION_RADII"
echo "  Dimension Diameters  : $DIMENSION_DIAMETERS"
echo "======================================================="
read -p "Do you want to continue? (Y/n): " confirm
if [[ "$confirm" != "Y" && "$confirm" != "y" && "$confirm" != "" ]]; then
    echo "Operation cancelled."
    exit 0
fi
echo ""

# --- CREATE CONFIGURATION FILE ---
echo "📝 Creating temporary configuration file..."
cat > "$CONFIG_FILE" << EOL
{
  "INPUT_FILE": "$INPUT_FILE",
  "TEMPLATE_FILE": "$TEMPLATE_FILE",
  "PROJECTION_METHOD": "$PROJECTION_METHOD",
  "DRAWING_STANDARD": "$DRAWING_STANDARD",
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
echo "✅ Created config.tmp.json"
echo ""

# --- EXECUTE WITH DOCKER ---
echo "🐳 Building Docker image (if necessary)..."
# Removed --no-cache flag for faster subsequent builds
if [[ "$(docker images -q freecad-automation-macro 2> /dev/null)" == "" ]]; then
  echo "🐳 Docker image not found. Building now..."
  docker build -t freecad-automation-macro "$PROJECT_ROOT"
else
  echo "🐳 Docker image already exists. Skipping build."
fi
echo ""

echo "🚀 Starting processing inside the container..."
docker run --rm \
  -v "$INPUT_DIR:/app/input" \
  -v "$TEMPLATE_DIR:/app/templates" \
  -v "$OUTPUT_DIR:/app/output" \
  -v "$SCRIPT_DIR:/app/scripts" \
  -v "$CONFIG_FILE:/app/config.json" \
  freecad-automation-macro

# Clean up config file after execution
rm -f "$CONFIG_FILE"

echo ""
echo "🎉🎉🎉 PROCESS COMPLETE! 🎉🎉🎉"
final_svg_file="$OUTPUT_DIR/final_drawing.svg"
if [[ -f "$final_svg_file" ]]; then
    echo "👀 Opening result file: $final_svg_file"
    # Use xdg-open for Linux, open for macOS, or start for Windows/WSL
    if command -v xdg-open > /dev/null; then
      xdg-open "$final_svg_file"
    elif command -v open > /dev/null; then
      open "$final_svg_file"
    elif command -v start > /dev/null; then
      start "$final_svg_file"
    else
      echo "Could not open the file automatically."
    fi
else
    echo "❌ Error: Final output file 'final_drawing.svg' not found."
fi