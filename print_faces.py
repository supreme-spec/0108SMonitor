"""Print faces with indices"""
import json

with open(r'batch_output\ep_ceiling_color_result.json') as f:
    data = json.load(f)

faces = data.get('faces', [])
print(f'Total faces: {len(faces)}')
for i, f in enumerate(faces):
    print(f'face[{i}]: path={f["path"]}, face_idx={f["face_idx"]}, cluster_id={f.get("cluster_id")}')
