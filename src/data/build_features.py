"""Construction des features - Version robuste"""
import pandas as pd
import numpy as np
from pathlib import Path

# Configuration
RAW_PATH = Path("data/raw/household_power_consumption.txt")
PROCESSED_PATH = Path("data/processed/cleaned_data.parquet")

def load_and_clean():
    """Charge et nettoie les données brutes"""
    print("📂 Chargement des données...")
    
    # Chargement sans parse_dates
    df = pd.read_csv(
        RAW_PATH, 
        sep=';', 
        low_memory=False,
        na_values=['?', 'nan', 'NULL']
    )
    
    # Création manuelle de datetime
    print("🕐 Création de la colonne datetime...")
    df['datetime'] = pd.to_datetime(
        df['Date'] + ' ' + df['Time'], 
        format='%d/%m/%Y %H:%M:%S',
        errors='coerce'
    )
    
    # Nettoyage dates invalides
    initial_len = len(df)
    df = df.dropna(subset=['datetime'])
    print(f"🗑️ Dates invalides supprimées : {initial_len - len(df)}")
    
    # Suppression colonnes originales
    df = df.drop(['Date', 'Time'], axis=1)
    
    # Réorganiser les colonnes
    cols = ['datetime'] + [c for c in df.columns if c != 'datetime']
    df = df[cols]
    
    # Nettoyage valeurs manquantes
    print(f"🧹 Valeurs manquantes totales : {df.isnull().sum().sum()}")
    
    # Supprimer lignes où target est manquante
    df = df.dropna(subset=['Global_active_power'])
    
    # Remplacer autres NaN par médiane
    for col in ['Global_reactive_power', 'Voltage', 'Global_intensity',
                'Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3']:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
    
    print(f"✅ Après nettoyage : {df.isnull().sum().sum()} valeurs manquantes")
    print(f"📅 Période : du {df['datetime'].min()} au {df['datetime'].max()}")
    print(f"📊 Dimensions : {df.shape}")
    
    return df

def create_time_features(df):
    """Crée les features temporelles"""
    df = df.copy()
    
    df['hour'] = df['datetime'].dt.hour
    df['day_of_week'] = df['datetime'].dt.dayofweek  # 0=lundi
    df['month'] = df['datetime'].dt.month
    df['weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # Features cycliques pour l'heure
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    
    print("⏰ Features temporelles ajoutées : hour, day_of_week, month, weekend, hour_sin, hour_cos")
    return df

def add_lagged_features(df, target_col='Global_active_power', lags=[1, 2, 3, 24]):
    """Ajoute les consommations passées"""
    df = df.copy().sort_values('datetime')
    
    for lag in lags:
        df[f'lag_{lag}h'] = df[target_col].shift(lag)
        print(f"   ✓ Lag {lag}h ajouté")
    
    df['rolling_24h_mean'] = df[target_col].rolling(24, min_periods=1).mean()
    print("   ✓ Rolling 24h mean ajouté")
    
    return df

def main():
    """Pipeline principal"""
    print("=" * 60)
    print("🏠 Construction des features - Prédiction consommation énergétique")
    print("=" * 60)
    
    # 1. Chargement
    df = load_and_clean()
    
    # 2. Features temporelles
    df = create_time_features(df)
    
    # 3. Features de lag
    df = add_lagged_features(df)
    
    # 4. Supprimer les NaN créés par les lags
    initial_len = len(df)
    df = df.dropna()
    print(f"\n🗑️ Lignes supprimées (NaN des lags) : {initial_len - len(df)}")
    
    # 5. Sauvegarde
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED_PATH, index=False)
    print(f"💾 Données sauvegardées : {PROCESSED_PATH}")
    print(f"📊 Dimensions finales : {df.shape}")
    
    # 6. Aperçu
    print("\n" + "=" * 60)
    print("🔍 APERÇU DES DONNÉES PRÉPARÉES")
    print("=" * 60)
    cols_to_show = ['datetime', 'Global_active_power', 'hour', 'day_of_week', 
                    'weekend', 'lag_1h', 'lag_24h', 'rolling_24h_mean']
    print(df[cols_to_show].head(10))
    
    # 7. Statistiques rapides
    print("\n📊 STATISTIQUES DE LA TARGET")
    print(f"   Moyenne : {df['Global_active_power'].mean():.2f} kWh")
    print(f"   Médiane : {df['Global_active_power'].median():.2f} kWh")
    print(f"   Max : {df['Global_active_power'].max():.2f} kWh")
    print(f"   Min : {df['Global_active_power'].min():.2f} kWh")
    
    return df

if __name__ == "__main__":
    df = main()