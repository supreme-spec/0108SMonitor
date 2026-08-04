"""Test PersonIntakePipeline"""
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
print(f'Image files: {[f.name for f in image_files]}')
print(f'Count: {len(image_files)}')
