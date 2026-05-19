cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code source
COPY src/ ./src/

# Exposer le port Render
EXPOSE 10000

# Commande pour démarrer l'API
CMD ["uvicorn", "src.api.predict_secure:app", "--host", "0.0.0.0", "--port", "10000"]
EOF