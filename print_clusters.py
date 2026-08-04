"""Print clusters"""
import json

folders = ['ep_ceiling_color', 'ep_ir_screen', 'ep_modern_osd']

for folder in folders:
    path = f'batch_output\\{folder}_result.json'
    with open(path) as f:
        data = json.load(f)
    
    print(f'{folder}:')
    for p in data.get('photos', []):
        faces = p.get('faces', [])
        print(f'  {p["filename"]}: {len(faces)} faces')
        for f in faces:
            print(f'    face {f["face_idx"]}: cluster_id={f.get("cluster_id")}')
    
    print(f'  clusters: {json.dumps(data.get("clusters", {}).get("clusters", {}), indent=4)}')
    print()
