import sys, csv
from pathlib import Path
import cv2, numpy as np
from PIL import Image, ImageOps
from insightface.app import FaceAnalysis
from insightface.utils import face_align

root = Path(sys.argv[1])
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)

models_path = str(Path(__file__).parent.parent / 'backend' / 'ai' / 'models' / 'models')
app = FaceAnalysis(name='buffalo_l', root=models_path, providers=['CPUExecutionProvider'])
app.prepare(ctx_id=-1, det_size=(1024, 1024))

rows = []

for p in sorted(root.rglob('*')):
    if p.suffix.lower() not in ('.jpg', '.jpeg', '.png'):
        continue
    
    pil = Image.open(p)
    if pil.mode in ('CMYK', 'P', 'RGBA', 'LA'):
        pil = pil.convert('RGB')
    pil = ImageOps.exif_transpose(pil)
    img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    
    faces = app.get(img)
    if not faces:
        for ds in (640, 1600):
            app.det_model.input_size = (ds, ds)
            faces = app.get(img)
            if faces:
                break
    
    for fi, f in enumerate(faces):
        x1, y1, x2, y2 = f.bbox.astype(int)
        crop = face_align.norm_crop(img, f.kps).copy()
        g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        blur = cv2.Laplacian(g, cv2.CV_64F).var()
        
        crop_path = out / f'{p.stem}_f{fi}.jpg'
        cv2.imwrite(str(crop_path), crop)
        
        rows.append([str(p.relative_to(root)), fi, round(float(f.det_score), 3),
                     x2 - x1, y2 - y1, round(float(blur), 1), round(float(g.mean()), 1)])

with open(out / 'inventory.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['file', 'face', 'det', 'w', 'h', 'blur_lap', 'bright'])
    w.writerows(rows)

print(f'faces found: {len(rows)}')
