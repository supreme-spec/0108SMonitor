"""Test ArchiveProcessor directly"""
import sys
sys.path.insert(0, 'backend')
from archive.processor import ArchiveProcessor

proc = ArchiveProcessor()
print(f'Processor initialized')

result = proc.process_folder(r'test_dataset\ep_ceiling_color', 'test')
print(f'Result: photos={len(result.get("photos", []))}, faces={len(result.get("faces", []))}')
for p in result.get('photos', []):
    print(f'  Photo {p["filename"]}: {len(p["faces"])} faces')
