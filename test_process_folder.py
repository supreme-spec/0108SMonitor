"""Test process_folder with logging"""
import sys
sys.path.insert(0, 'backend')
from archive.processor import ArchiveProcessor
from pathlib import Path

proc = ArchiveProcessor()
folder_path = r'test_dataset\ep_ceiling_color'
folder = Path(folder_path)

image_files = sorted([
    f for f in folder.iterdir()
    if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp')
])
print(f'Image files: {[f.name for f in image_files]}')

for img_path in image_files:
    print(f'Processing {img_path.name}...')
    try:
        result = proc._process_image(img_path)
        print(f'  OK: {len(result["faces"])} faces')
    except Exception as e:
        print(f'  ERROR: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
