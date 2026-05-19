"""API sécurisée de prédiction avec clé API et rate limiting"""
from fastapi import FastAPI, HTTPException, Depends, Request # type: ignore
from fastapi.security import APIKeyHeader # type: ignore
from pydantic import BaseModel, Field # type: ignore
from datetime import datetime, timedelta
from typing import Optional, Dict
import uvicorn # type: ignore
import time
import logging
from collections import defaultdict

# Configuration
API_KEY = "energy_prediction_2024_secret_key"  # À changer et mettre dans .env en production
API_KEY_NAME = "X-API-Key"

# Sécurité
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# Rate limiting (stockage simple en mémoire – pour démo)
rate_limit_storage: Dict[str, list] = defaultdict(list)
RATE_LIMIT = 100  # Requêtes max
RATE_LIMIT_WINDOW = 60  # Par fenêtre de 60 secondes

# Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application
app = FastAPI(
    title="API Prédiction Énergétique (Sécurisée)",
    description="API avec authentification et rate limiting",
    version="2.0.0"
)

# Modèles Pydantic
class PredictionRequest(BaseModel):
    last_hour_consumption: float = Field(
        ..., 
        ge=0, 
        le=50,
        description="Consommation de la dernière heure (kWh)",
        example=2.45
    )
    building_id: Optional[str] = None

class PredictionResponse(BaseModel):
    prediction: float
    model_used: str
    confidence: float
    latency_ms: float
    timestamp: datetime

class ErrorResponse(BaseModel):
    detail: str
    timestamp: datetime

# ========== FONCTIONS D'AUTHENTIFICATION ==========

def verify_api_key(api_key: str = Depends(api_key_header)):
    """Vérifie que la clé API est valide"""
    if api_key != API_KEY:
        logger.warning(f"Tentative d'accès avec clé invalide: {api_key[:10]}...")
        raise HTTPException(
            status_code=403,
            detail="Clé API invalide"
        )
    return api_key

def check_rate_limit(request: Request):
    """Vérifie que le client n'a pas dépassé sa limite de requêtes"""
    client_ip = request.client.host
    now = time.time()
    
    # Nettoyer les anciennes requêtes
    rate_limit_storage[client_ip] = [
        t for t in rate_limit_storage[client_ip] 
        if now - t < RATE_LIMIT_WINDOW
    ]
    
    # Vérifier la limite
    if len(rate_limit_storage[client_ip]) >= RATE_LIMIT:
        logger.warning(f"Rate limit dépassé pour {client_ip}")
        raise HTTPException(
            status_code=429,
            detail=f"Trop de requêtes. Limite: {RATE_LIMIT} par {RATE_LIMIT_WINDOW} secondes"
        )
    
    # Ajouter la requête courante
    rate_limit_storage[client_ip].append(now)
    return True

# ========== ENDPOINTS ==========

@app.get("/", tags=["Info"])
async def root():
    return {
        "message": "API Prédiction Énergie (Sécurisée)",
        "version": "2.0.0",
        "authentication": "API Key required",
        "rate_limit": f"{RATE_LIMIT} req / {RATE_LIMIT_WINDOW}s",
        "docs": "/docs"
    }

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Vérifie que l'API tourne"""
    return {
        "status": "healthy",
        "model": "persistance",
        "timestamp": datetime.now()
    }

@app.get("/metrics", tags=["Monitoring"])
async def get_metrics(api_key: str = Depends(verify_api_key)):
    """Retourne des métriques sur l'utilisation (nécessite authentification)"""
    return {
        "active_clients": len(rate_limit_storage),
        "rate_limit_window": RATE_LIMIT_WINDOW,
        "rate_limit_max": RATE_LIMIT,
        "timestamp": datetime.now()
    }

@app.post("/predict", 
          response_model=PredictionResponse,
          dependencies=[Depends(check_rate_limit)],
          tags=["Prediction"])
async def predict(
    request: PredictionRequest,
    api_key: str = Depends(verify_api_key),
    http_request: Request = None
):
    """
    Prédiction sécurisée avec :
    - Clé API obligatoire
    - Rate limiting
    - Logs structurés
    """
    start_time = time.time()
    client_ip = http_request.client.host if http_request else "unknown"
    
    # Log de la requête
    logger.info(f"Requête - IP: {client_ip}, conso: {request.last_hour_consumption} kWh")
    
    # ----- MODÈLE (persistance) -----
    prediction = request.last_hour_consumption
    
    # Calcul du niveau de confiance
    if request.last_hour_consumption < 0.5:
        confidence = 95.0
    elif request.last_hour_consumption < 2.0:
        confidence = 90.0
    elif request.last_hour_consumption < 10.0:
        confidence = 80.0
    else:
        confidence = 60.0
    
    # Calcul de la latence
    latency = (time.time() - start_time) * 1000
    
    logger.info(f"Réponse - prédiction: {prediction:.3f} kWh, latence: {latency:.1f}ms")
    
    return PredictionResponse(
        prediction=prediction,
        model_used="persistance",
        confidence=confidence,
        latency_ms=latency,
        timestamp=datetime.now()
    )

@app.post("/predict/batch", tags=["Prediction"])
async def predict_batch(
    requests: list[PredictionRequest],
    api_key: str = Depends(verify_api_key)
):
    """Prédiction batch – plusieurs bâtiments en une requête"""
    results = []
    for req in requests:
        results.append({
            "last_hour_consumption": req.last_hour_consumption,
            "prediction": req.last_hour_consumption,  # Modèle persistance
            "building_id": req.building_id
        })
    
    return {
        "model": "persistance",
        "count": len(results),
        "predictions": results
    }

if __name__ == "__main__":
    uvicorn.run(
        "predict_secure:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )