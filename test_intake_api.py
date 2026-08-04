"""Test intake API endpoint"""
import requests
import json

# Test intake endpoint
url = "http://localhost:8002/intake"
data = {
    "folder": r"D:\bd_gosti\test_dataset",
    "person_name": "Test Person"
}

print(f"Calling intake API: {url}")
print(f"Parameters: {json.dumps(data, indent=2)}")

try:
    response = requests.post(url, data=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResult summary:")
        print(f"  photos_count: {result.get('photos_count', 0)}")
        print(f"  photos_processed: {result.get('photos_processed', 0)}")
        print(f"  photos_passed_quality: {result.get('photos_passed_quality', 0)}")
        print(f"  photos_duplicate: {result.get('photos_duplicate', 0)}")
        print(f"  photos_diversity_selected: {result.get('photos_diversity_selected', 0)}")
        print(f"  embeddings_generated: {result.get('embeddings_generated', 0)}")
        print(f"  status: {result.get('status', 'unknown')}")
        print(f"\nFull result: {json.dumps(result, indent=2, default=str)}")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Exception: {e}")
