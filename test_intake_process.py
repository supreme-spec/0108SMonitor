"""Test PersonIntakePipeline._process_single_image"""
import sys
sys.path.insert(0, 'backend')
from archive.intake import PersonIntakePipeline
from pathlib import Path

pipeline = PersonIntakePipeline()
folder_path = r'test_dataset\enrollment'
folder = Path(folder_path)

image_files = sorted([
    f for f in folder.iterdir()
    if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp')
])

for img_path in image_files:
    print(f'Processing {img_path.name}...')
    try:
        result = pipeline._process_single_image(img_path, 'test_person')
        print(f'  Result: {result["status"]}')
        if result["status"] != "passed":
            print(f'  Reason: {result.get("reason", "N/A")}')
    except Exception as e:
        print(f'  ERROR: {type(e).__name__}: {e}')
