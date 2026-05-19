# """Vérification rapide que les données sont exploitables"""
import pandas as pd
import os

# Charger les données brutes
raw_path = "data/raw/household_power_consumption.txt"
df = pd.read_csv(raw_path, sep=';', low_memory=False)

print("✅ Données chargées avec succès")
print(f"📊 Dimensions : {df.shape}")
print(f"📅 Période : de {df['Date'].iloc[0]} à {df['Date'].iloc[-1]}")
print(f"🔢 Colonnes : {list(df.columns)}")
print(f"⚠️  Valeurs manquantes : {df.isnull().sum().sum()}")

# Sauvegarder un échantillon pour exploration rapide
sample = df.head(1000)
sample.to_csv("data/processed/sample_1000.csv", index=False)
print("✅ Échantillon sauvegardé dans data/processed/")