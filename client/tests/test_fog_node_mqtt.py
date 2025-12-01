import paho.mqtt.client as mqtt
import json
import time
import random

BROKER = "192.168.1.158"  # IP de la machine Cloud
PORT = 1883
TOPIC = "fraud_alerts"

NODE_NAME = "Fog_Node_1"

# Création client MQTT
client = mqtt.Client(NODE_NAME)
client.connect(BROKER, PORT)
client.loop_start()  # start loop in background

# Exemple de transaction simulée
def generate_transaction():
    return {
        "id": random.randint(1000, 9999),
        "amount": round(random.uniform(10, 1000), 2),
        "account": f"AC{random.randint(100,999)}",
        "label": "fraud"  # ou "legit"
    }

# Envoi d'alerte
def send_alert(transaction):
    alert = {
        "node": NODE_NAME,
        "transaction": transaction
    }
    client.publish(TOPIC, json.dumps(alert))
    print(f"[{NODE_NAME}] Alert sent: {transaction}")

# Simulation d'envoi d'alertes toutes les 5 secondes
while True:
    tx = generate_transaction()
    if tx["label"] == "fraud":  # simulate detection
        send_alert(tx)
    time.sleep(5)
