"""API de prédiction - Modèle de persistance (lag_1h)
   Déploiement d'un modèle ML en production
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uvicorn
import time
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation de l'application
app = FastAPI(
    title="API Prédiction Consommation Énergétique",
    description="Prédiction basée sur le modèle de persistance (lag_1h)",
    version="1.0.0"
)

# Modèles de données (Pydantic)
class PredictionRequest(BaseModel):
    """Structure de la requête entrante"""
    last_hour_consumption: float = Field(
        ..., 
        ge=0,  # greater or equal to 0
        le=50,  # less or equal to 50 (valeur max raisonnable)
        description="Consommation de la dernière heure en kWh",
        example=2.45
    )
    building_id: Optional[str] = Field(
        None, 
        description="Identifiant du bâtiment (optionnel)"
    )
    timestamp: Optional[datetime] = Field(
        None, 
        description="Timestamp de la requête (auto si non fourni)"
    )

class PredictionResponse(BaseModel):
    """Structure de la réponse"""
    prediction: float = Field(..., description="Prédiction pour la prochaine heure (kWh)")
    model_used: str = Field(..., description="Nom du modèle utilisé")
    confidence: float = Field(..., description="Niveau de confiance (basé sur erreur historique)")
    latency_ms: float = Field(..., description="Temps de calcul en millisecondes")
    timestamp: datetime = Field(..., description="Timestamp de la réponse")

class HealthResponse(BaseModel):
    """Structure du health check"""
    status: str
    model: str
    uptime_seconds: float

# Variables globales (simulent l'état du service)
start_time = time.time()
historical_mae = 0.072  # MAE de notre baseline sur le test set

@app.on_event("startup")
async def startup_event():
    """Actions au démarrage de l'API"""
    logger.info("🚀 API de prédiction énergétique démarrée")
    logger.info(f"📊 Modèle chargé : persistance (lag_1h) avec MAE historique = {historical_mae} kWh")

@app.get("/", tags=["Health"])
async def root():
    """Endpoint racine – informations générales"""
    return {
        "message": "API Prédiction Énergie - Modèle Baseline",
        "model": "persistance (lag_1h)",
        "version": "1.0.0",
        "docs": "/docs"  # Documentation interactive
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Vérifie que l'API est opérationnelle"""
    uptime = time.time() - start_time
    return HealthResponse(
        status="healthy",
        model="persistance",
        uptime_seconds=uptime
    )

@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: PredictionRequest, http_request: Request):
    """
    Prédiction basée sur la persistance.
    
    Règle métier : la meilleure prédiction de la prochaine heure
    est la consommation de la dernière heure.
    
    - Si consommation < 0.5 kWh (nuit) → confiance élevée
    - Si consommation > 10 kWh (pic) → confiance réduite
    """
    start_time_request = time.time()
    
    # Log de la requête (pour monitoring)
    client_ip = http_request.client.host
    logger.info(f"Requête reçue de {client_ip} - conso dernière heure: {request.last_hour_consumption} kWh")
    
    # Validation supplémentaire (Pydantic fait déjà l'essentiel)
    if request.last_hour_consumption > 20:
        logger.warning(f"Consommation anormalement élevée: {request.last_hour_consumption} kWh")
    
    # ----- LE MODÈLE -----
    # Version production : persistance (lag_1h)
    prediction = request.last_hour_consumption
    # --------------------
    
    # Calcul du niveau de confiance
    # Moins la conso est prévisible, plus la confiance baisse
    if request.last_hour_consumption < 0.5:
        confidence = 95.0  # Nuit – très stable
    elif request.last_hour_consumption < 2.0:
        confidence = 90.0  # Période normale
    elif request.last_hour_consumption < 10.0:
        confidence = 80.0  # Période active
    else:
        confidence = 60.0  # Pic de consommation – moins fiable
    
    # Calcul de la latence
    latency = (time.time() - start_time_request) * 1000  # en millisecondes
    
    logger.info(f"Prédiction retournée: {prediction:.3f} kWh (confiance {confidence:.1f}%, latence {latency:.1f}ms)")
    
    return PredictionResponse(
        prediction=prediction,
        model_used="persistance",
        confidence=confidence,
        latency_ms=latency,
        timestamp=datetime.now()
    )

# Endpoint pour prédictions batch (bonne pratique pour l'efficacité)
@app.post("/predict/batch", tags=["Prediction"])
async def predict_batch(requests: list[PredictionRequest]):
    """
    Prédiction en batch pour plusieurs bâtiments ou heures.
    Plus efficace que d'appeler /predict plusieurs fois.
    """
    predictions = []
    for req in requests:
        pred = req.last_hour_consumption
        predictions.append({
            "last_hour_consumption": req.last_hour_consumption,
            "prediction": pred,
            "building_id": req.building_id
        })
    
    return {
        "model": "persistance",
        "count": len(predictions),
        "predictions": predictions
    }

if __name__ == "__main__":
    uvicorn.run(
        "predict:app",
        host="0.0.0.0",
        port=8003,
        reload=True,  # Mode développement – se relance à chaque modification
        log_level="info"
    )