import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    print("Testing /api/health...")
    try:
        res = requests.get(f"{BASE_URL}/api/health")
        print(f"Status: {res.status_code}")
        print(f"Response: {res.json()}")
    except Exception as e:
        print(f"Error: {e}")

def test_translate():
    print("\nTesting /api/translate...")
    try:
        res = requests.post(
            f"{BASE_URL}/api/translate",
            json={"texts": ["hello", "world"], "source_lang": "en", "target_lang": "hi"}
        )
        print(f"Status: {res.status_code}")
        print(f"Response: {res.json()}")
    except Exception as e:
        print(f"Error: {e}")

def test_generate():
    print("\nTesting /api/generate-itinerary...")
    try:
        res = requests.post(
            f"{BASE_URL}/api/generate-itinerary",
            json={
                "destination": "Goa",
                "start_date": "2026-10-01",
                "end_date": "2026-10-05",
                "budget": 50000,
                "travelers": 2,
                "preferences": ["beaches", "nightlife"],
                "accommodation_preference": "mid-range"
            }
        )
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            success = data.get("success")
            print(f"Success Flag: {success}")
            if "data" in data and "budget_summary" in data["data"]:
                print("Budget summary found.")
        else:
            print(f"Response: {res.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_health()
    test_translate()
    test_generate()
