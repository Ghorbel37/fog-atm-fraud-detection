import os
import pandas as pd
import joblib
import paho.mqtt.client as mqtt

# ---------- CONFIGURATION ----------
MODEL_PATH = "models/best_model_random_forest.pkl"  # Chemin vers ton modèle
DATA_PATH = "data/simulation_node_1.csv"  # Dataset à traiter
SCALER_PATH = "models/scaler.pkl"

MQTT_BROKER = "192.168.1.158"  # Remplace par ton broker MQTT
MQTT_PORT = 1883
TOPIC_RESULTS = "fog/transactions/results"
TOPIC_RAW = "fog/transactions/raw"

# ---------- FONCTIONS ----------
def load_model(path):
    """Charge le modèle depuis un fichier .pkl"""
    return joblib.load(path)

def connect_mqtt(broker, port):
    """Connecte le client MQTT"""
    client = mqtt.Client("123")
    client.connect(broker, port)
    return client

def publish(client, topic, message):
    """Publie un message sur un topic MQTT"""
    client.publish(topic, message)

def main():
    # Charger le modèle
    model = load_model(MODEL_PATH)
    print(f"Model loaded from {MODEL_PATH}")

    # Charger le dataset
    df = pd.read_csv(DATA_PATH)
    print(f"Dataset loaded from {DATA_PATH}, shape: {df.shape}")

    # Connecter le client MQTT
    mqtt_client = connect_mqtt(MQTT_BROKER, MQTT_PORT)
    print(f"Connected to MQTT broker {MQTT_BROKER}:{MQTT_PORT}")

    # Publier les données brutes
    for _, row in df.iterrows():
        publish(mqtt_client, TOPIC_RAW, row.to_json())

    # Charger le scaler
    scaler = joblib.load(SCALER_PATH)
    print(f"Scaler loaded from {SCALER_PATH}")

    # Préparer les features pour le modèle (tout sauf "Class" et "Time")
    X = df.drop(columns=["Class"])

    # Appliquer le scaler
    X_scaled = scaler.transform(X)

    # Prédire avec le modèle
    predictions = model.predict(X_scaled)

    # Publier les résultats
    for idx, pred in enumerate(predictions):
        message = {"Time": int(df.iloc[idx]["Time"]), "Prediction": int(pred)}
        publish(mqtt_client, TOPIC_RESULTS, str(message))

    print("All data and predictions published to MQTT topics.")

    # Déconnecter le client
    mqtt_client.disconnect()

if __name__ == "__main__":
    main()
