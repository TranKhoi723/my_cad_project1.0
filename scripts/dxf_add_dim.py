import ezdxf, json, os

base = os.environ.get("OUTPUT_BASE", "output")
dxf_path = f"/app/output/{base}.dxf"
json_path = f"/app/output/{base}_coords.json"
dxf_out = f"/app/output/{base}_with_dim.dxf"

doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

with open(json_path) as f:
    data = json.load(f)

for d in data["dimensions"]:
    p1 = d["p1"]
    p2 = d["p2"]
    offset = d["offset"]
    msp.add_linear_dim(
        base=((p1[0] + p2[0]) / 2, p1[1] + offset),
        p1=p1,
        p2=p2,
        angle=0
    ).render()

doc.saveas(dxf_out)
print(f"✅ DXF with dim saved: {dxf_out}")
