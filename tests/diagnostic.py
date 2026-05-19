# diagnostic.py
import requests

API_URL = "http://localhost:8003"

print("🔍 Diagnostic de l'API sécurisée")
print("=" * 40)

# Test 1 : Sans clé
print("\n1. Requête SANS clé API :")
resp = requests.post(f"{API_URL}/predict", json={"last_hour_consumption": 2.45})
print(f"   Status code: {resp.status_code}")
print(f"   Réponse: {resp.text}")

# Test 2 : Clé invalide
print("\n2. Requête AVEC clé invalide :")
headers = {"X-API-Key": "fausse_cle"}
resp = requests.post(f"{API_URL}/predict", headers=headers, json={"last_hour_consumption": 2.45})
print(f"   Status code: {resp.status_code}")
print(f"   Réponse: {resp.text}")

# Test 3 : Clé valide
print("\n3. Requête AVEC clé valide :")
API_KEY = "energy_prediction_2024_secret_key"
headers = {"X-API-Key": API_KEY}
resp = requests.post(f"{API_URL}/predict", headers=headers, json={"last_hour_consumption": 2.45})
print(f"   Status code: {resp.status_code}")
if resp.status_code == 200:
    print(f"   Réponse: {resp.json()}")
else:
    print(f"   Réponse: {resp.text}")