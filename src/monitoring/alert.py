"""Système d'alerte basé sur les logs"""
import re
import time
from datetime import datetime
from collections import deque

class APIMonitor:
    def __init__(self, error_threshold=5, time_window=60):
        self.errors = deque(maxlen=100)
        self.error_threshold = error_threshold
        self.time_window = time_window
        self.last_alert = 0
        self.alert_cooldown = 300  # 5 minutes entre alertes
    
    def log_request(self, status_code, latency_ms):
        """Enregistre une requête"""
        self.errors.append({
            "timestamp": time.time(),
            "status_code": status_code,
            "latency_ms": latency_ms
        })
    
    def check_alerts(self):
        """Vérifie si des alertes doivent être déclenchées"""
        now = time.time()
        
        # Compter les erreurs récentes (status >= 400)
        recent_errors = [
            e for e in self.errors 
            if now - e["timestamp"] <= self.time_window and e["status_code"] >= 400
        ]
        
        # Compter les requêtes lentes (latence > 100ms)
        slow_requests = [
            e for e in self.errors 
            if now - e["timestamp"] <= self.time_window and e["latency_ms"] > 100
        ]
        
        alerts = []
        
        # Alerte 1 : trop d'erreurs
        if len(recent_errors) >= self.error_threshold:
            if now - self.last_alert > self.alert_cooldown:
                alerts.append(f"🚨 ALERTE: {len(recent_errors)} erreurs en {self.time_window}s")
                self.last_alert = now
        
        # Alerte 2 : latence élevée
        if len(slow_requests) > 10:
            alerts.append(f"⚠️ LATENCE ÉLEVÉE: {len(slow_requests)} requêtes lentes")
        
        # Alerte 3 : taux d'erreur
        if len(self.errors) > 0:
            error_rate = len(recent_errors) / len(self.errors) * 100
            if error_rate > 10:  # Plus de 10% d'erreurs
                alerts.append(f"📉 TAUX D'ERREUR: {error_rate:.1f}%")
        
        return alerts

# Exemple d'utilisation
if __name__ == "__main__":
    monitor = APIMonitor()
    
    print("📊 Simulation de monitoring (Ctrl+C pour arrêter)")
    try:
        while True:
            # Simule des requêtes (à remplacer par la vraie analyse des logs)
            import random
            status = random.choices([200, 200, 200, 400, 500], weights=[0.9, 0.05, 0.03, 0.01, 0.01])[0]
            latency = random.uniform(1, 150)
            
            monitor.log_request(status, latency)
            alerts = monitor.check_alerts()
            
            for alert in alerts:
                print(f"{datetime.now().strftime('%H:%M:%S')} - {alert}")
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n👋 Monitoring arrêté")