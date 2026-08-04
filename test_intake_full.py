"""Test PersonIntakePipeline._process_single_image full"""
import sys
sys.path.insert(0, 'backend')
from archive.intake import PersonIntakePipeline

pipeline = PersonIntakePipeline()

img_path = r'test_dataset\enrollment\person1_photo1.jpg'

result = pipeline._process_single_image(img_path, 'test_person')
print(f'Result: {result["status"]}')
if result["status"] != "passed":
    print(f'Reason: {result["reason"]}')
    print(f'Metrics: {result.get("metrics", {})}')
