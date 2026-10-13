import os
import pandas as pd
import joblib
import paho.mqtt.client as mqtt
import json
import time
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText

# Charger le fichier .env
load_dotenv()

# ---------- CONFIGURATION ----------
# Each value can be overridden with an environment variable of the same name.
NODE_ID = os.getenv("NODE_ID", "Fog_Node_1")
MODEL_PATH = os.getenv("MODEL_PATH", "models/best_model_random_forest.pkl")
SCALER_PATH = os.getenv("SCALER_PATH", "models/scaler.pkl")
DATA_PATH = os.getenv("DATA_PATH", "data/simulation_node_1.csv")

MQTT_BROKER = os.getenv("MQTT_BROKER", "192.168.1.159")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_RESULTS = "fog/transactions/results"
TOPIC_RAW = "fog/transactions/raw"

SEND_INTERVAL = float(os.getenv("SEND_INTERVAL", "1"))  # seconds between rows

# --- CONFIG EMAIL ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
EMAIL_ENABLED = all([SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL])


# ---------- FONCTION ENVOI EMAIL ----------
def send_email(subject, message):
    """Envoie un email via SMTP."""
    if not EMAIL_ENABLED:
        return
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()

        print("📧 Email sent successfully!")

    except Exception as e:
        print("❌ Failed to send email:", e)


# ---------- FONCTIONS MQTT ----------
def load_model(path):
    return joblib.load(path)

def connect_mqtt(broker, port):
    client = mqtt.Client(NODE_ID)
    client.connect(broker, port)
    return client

def publish(client, topic, message):
    client.publish(topic, json.dumps(message))


# ---------- MAIN ----------
def main():
    if not EMAIL_ENABLED:
        print("Email alerts disabled (set SENDER_EMAIL, SENDER_PASSWORD and RECEIVER_EMAIL to enable).")

    model = load_model(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    df = pd.read_csv(DATA_PATH)

    mqtt_client = connect_mqtt(MQTT_BROKER, MQTT_PORT)

    X = df.drop(columns=["Class"])
    X_scaled = scaler.transform(X)
    predictions = model.predict(X_scaled)

    for idx, row in df.iterrows():

        # ----- Envoi des données brutes -----
        data_row = row.drop("Class").to_dict()
        data_row["Node_ID"] = NODE_ID
        publish(mqtt_client, TOPIC_RAW, data_row)

        # ----- Prediction -----
        prediction = int(predictions[idx])
        result_message = {
            "Node_ID": NODE_ID,
            "Time": int(row["Time"]),
            "Prediction": prediction
        }
        publish(mqtt_client, TOPIC_RESULTS, result_message)

        print(f"[{NODE_ID}] Sent row {idx+1} - Prediction = {prediction}")

        # ----- Envoi EMAIL si fraude détectée -----
        if prediction == 1:
            email_subject = f"🚨 FRAUD ALERT from {NODE_ID}"
            email_body = f"""
Une transaction frauduleuse a été détectée !

Node ID : {NODE_ID}
Time : {int(row['Time'])}
Transaction index : {idx}

Données de la transaction :
{json.dumps(data_row, indent=4)}
"""
            send_email(email_subject, email_body)

        # Pause entre les lignes
        time.sleep(SEND_INTERVAL)

    mqtt_client.disconnect()
    print("All data processed.")


if __name__ == "__main__":
    main()
