# scripts/pipeline.py
import os, subprocess, sys, json

def run_command(command):
    print(f"--- Running command: {' '.join(command)} ---")
    subprocess.run(command, check=True)

def main():
    print("🚀 Starting pipeline process...")
    with open("/app/config.json", 'r') as f:
        config = json.load(f)

    print("ℹ️ Configuration received from config.json:")
    for key, value in config.items():
        print(f"  {key}: {value}")

    template_path = f"/app/templates/{config['TEMPLATE_FILE']}"
    project_input = "/app/output/step2_with_dims.dxf"
    project_output = "/app/output/projections_only.svg"

    try:
        # Step 1: FreeCAD - Create DXF from STEP and Template
        run_command(["xvfb-run", "freecadcmd", "/app/scripts/freecad_techdraw_core.py"])

        # Step 2: Add dimensions using ezdxf
        run_command(["python", "/app/scripts/dxf_add_dim.py"])

        # Step 3: Render and merge SVG template
        run_command(["python", "/app/scripts/dxf_render_svg.py", template_path])

        print("✅ Pipeline inside container completed successfully!")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
