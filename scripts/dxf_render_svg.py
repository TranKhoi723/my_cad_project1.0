import ezdxf, os
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.cairosvg import CairoSvgBackend

base = os.environ.get("OUTPUT_BASE", "output")
dxf_file = f"/app/output/{base}_with_dim.dxf"
svg_out = f"/app/output/{base}.svg"
svg_template = f"/app/templates/template_a4.svg"

doc = ezdxf.readfile(dxf_file)
ctx = RenderContext(doc)
backend = CairoSvgBackend()
Frontend(ctx, backend).draw_layout(doc.modelspace())
drawing_svg = backend.get_string()

with open(svg_template, 'r', encoding='utf-8') as f:
    template = f.read()

final_svg = template.replace("<!--DRAWING_CONTENT-->", drawing_svg)

with open(svg_out, 'w', encoding='utf-8') as f:
    f.write(final_svg)

print(f"✅ SVG generated: {svg_out}")
