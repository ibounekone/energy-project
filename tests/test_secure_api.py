"""Tests de l'API sécurisée"""
import requests
import time

API_URL = "http://localhost:8003"
API_KEY = "energy_prediction_2024_secret_key"
HEADERS = {"X-API-Key": API_KEY}

def test_missing_key():
    """Test sans clé API – doit échouer avec 401 ou 403"""
    response = requests.post(f"{API_URL}/predict", json={"last_hour_consumption": 2.45})
    print(f"Sans clé : {response.status_code}")
    # FastAPI retourne 403 avec APIKeyHeader, mais ça peut varier
    assert response.status_code in [401, 403]  # ← ACCEPTE LES DEUX

def test_invalid_key():
    """Test avec clé invalide"""
    headers = {"X-API-Key": "mauvaise_cle"}
    response = requests.post(f"{API_URL}/predict", headers=headers, json={"last_hour_consumption": 2.45})
    print(f"Clé invalide : {response.status_code}")
    assert response.status_code in [401, 403]

def test_valid_key():
    """Test avec clé valide"""
    response = requests.post(f"{API_URL}/predict", headers=HEADERS, json={"last_hour_consumption": 2.45})
    print(f"Clé valide : {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    print(f"   Prédiction : {data['prediction']} kWh")
    print(f"   Confiance : {data['confidence']}%")
    print(f"   Latence : {data['latency_ms']:.2f} ms")

def test_rate_limit():
    """Test le rate limiting – envoie plus de requêtes que la limite"""
    print("\nTest rate limiting (101 requêtes) ...")
    success = 0
    errors = 0
    rate_limit_hit = False
    
    for i in range(101):
        response = requests.post(f"{API_URL}/predict", headers=HEADERS, json={"last_hour_consumption": 1.0})
        if response.status_code == 200:
            success += 1
        elif response.status_code == 429:  # Too Many Requests
            errors += 1
            if not rate_limit_hit:
                print(f"   🚦 Rate limit atteint à la requête {i+1}")
                rate_limit_hit = True
        time.sleep(0.01)  # Petite pause pour éviter de surcharger
    
    print(f"✅ Réussies : {success}, ❌ Bloquées : {errors}")
    assert errors > 0, "Le rate limiting n'a pas fonctionné"

def test_metrics():
    """Test l'endpoint métriques (nécessite auth)"""
    response = requests.get(f"{API_URL}/metrics", headers=HEADERS)
    print(f"Métriques : {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Clients actifs : {data.get('active_clients', 'N/A')}")
        print(f"   Limite : {data.get('rate_limit_max', 'N/A')}/s")

def test_health():
    """Test health check (public, sans auth)"""
    response = requests.get(f"{API_URL}/health")
    print(f"Health check : {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    print(f"   Status : {data.get('status')}")

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 TESTS API SÉCURISÉE")
    print("=" * 50)
    
    # Vérifier que l'API tourne
    try:
        requests.get(f"{API_URL}/health", timeout=2)
        print("✅ API accessible")
    except requests.exceptions.ConnectionError:
        print("❌ API non accessible. Lance d'abord : python src/api/predict_secure.py")
        exit(1)
    except Exception as e:
        print(f"❌ Erreur : {e}")
        exit(1)
    
    test_health()
    test_missing_key()
    test_invalid_key()
    test_valid_key()
    test_metrics()
    
    # test_rate_limit()  # Décommenter pour tester le rate limiting (prend ~5 secondes)
    
    print("\n" + "=" * 50)
    print("✅ Tous les tests passés !")
    print("=" * 50)