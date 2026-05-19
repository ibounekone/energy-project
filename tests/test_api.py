"""Tests de l'API de prédiction"""
import requests
import json
import time

API_URL = "http://localhost:8003"

def test_health():
    """Test l'endpoint /health"""
    response = requests.get(f"{API_URL}/health")
    print(f"Health: {response.json()}")
    assert response.status_code == 200

def test_predict():
    """Test l'endpoint /predict"""
    payload = {"last_hour_consumption": 2.45}
    response = requests.post(f"{API_URL}/predict", json=payload)
    result = response.json()
    
    print(f"\n📊 Prédiction :")
    print(f"   Consommation prédite : {result['prediction']} kWh")
    print(f"   Modèle : {result['model_used']}")
    print(f"   Confiance : {result['confidence']}%")
    print(f"   Latence : {result['latency_ms']:.2f} ms")
    
    assert response.status_code == 200
    assert result['prediction'] == 2.45  # Le modèle persistance

def test_batch():
    """Test l'endpoint batch"""
    payload = [
        {"last_hour_consumption": 1.23, "building_id": "A"},
        {"last_hour_consumption": 4.56, "building_id": "B"},
        {"last_hour_consumption": 0.89, "building_id": "C"}
    ]
    response = requests.post(f"{API_URL}/predict/batch", json=payload)
    result = response.json()
    
    print(f"\n📦 Batch : {result['count']} prédictions")
    for pred in result['predictions']:
        print(f"   {pred['building_id']}: {pred['prediction']} kWh")
    
    assert response.status_code == 200

def test_invalid():
    """Test une requête invalide (consommation négative)"""
    payload = {"last_hour_consumption": -5}
    response = requests.post(f"{API_URL}/predict", json=payload)
    print(f"\n❌ Requête invalide : {response.status_code}")
    assert response.status_code == 422  # Unprocessable Entity

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 TESTS DE L'API")
    print("=" * 50)
    
    # Vérifier que l'API tourne
    try:
        test_health()
        print("✅ API accessible")
    except:
        print("❌ API non accessible. Lance d'abord : python src/api/predict.py")
        exit(1)
    
    test_predict()
    test_batch()
    test_invalid()
    
    print("\n✅ Tous les tests passés !")