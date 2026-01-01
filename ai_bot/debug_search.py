import os
import json
from dotenv import load_dotenv
import ai_db_helper as db_helper

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

def test_search(query):
    print(f"\n--- Testing Search: '{query}' ---")
    results_json = db_helper.search(query)
    results = json.loads(results_json)
    if not results:
        print("Nothing found.")
    for idx, p in enumerate(results, 1):
        status = "✅" if any(i.get('quantity', 0) > 0 for i in p.get('inventory', [])) else "⏳"
        print(f"{idx}. {p['name']} (ID: {p['id']}) - {p['price']} {status}")

if __name__ == "__main__":
    test_search("палто?")
    test_search("пальто")
    test_search("ветровка")
