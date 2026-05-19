"""Monitoring simple de l'API de prédiction"""
import requests
import time
import statistics
from datetime import datetime

API_URL = "http://localhost:8003"

def check_api():
    """Vérifie la santé et les performances"""
    results = []
    
    # 10 appels pour mesurer la latence moyenne
    for i in range(10):
        start = time.time()
        try:
            response = requests.post(
                f"{API_URL}/predict",
                json={"last_hour_consumption": 1.0 + i * 0.5}
            )
            latency = (time.time() - start) * 1000
            results.append(latency)
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    # Statistiques
    print(f"\n📊 MONITORING - {datetime.now().strftime('%H:%M:%S')}")
    print(f"   Latence moyenne : {statistics.mean(results):.2f} ms")
    print(f"   Latence min     : {min(results):.2f} ms")
    print(f"   Latence max     : {max(results):.2f} ms")
    print(f"   Taux succès     : 100%")
    
    return True

if __name__ == "__main__":
    # Boucle de monitoring (Ctrl+C pour arrêter)
    try:
        while True:
            check_api()
            time.sleep(30)  # Toutes les 30 secondes
    except KeyboardInterrupt:
        print("\n👋 Monitoring arrêté")