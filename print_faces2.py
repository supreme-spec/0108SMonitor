"""Print faces with indices - v2"""
import json

with open(r'batch_output\ep_ceiling_color_result.json') as f:
    data = json.load(f)

print('photos:')
for p in data.get('photos', []):
    print(f'  {p["filename"]}:')
    for i, f in enumerate(p.get('faces', [])):
        print(f'    face[{i}]: face_idx={f["face_idx"]}, cluster_id={f.get("cluster_id")}, bbox={f["bbox"]}')
