# Fog Node Client

This is the client-side application for the Fog ATM Fraud Detection System. Each fog node acts as an edge computing device that processes credit card transactions locally using a pre-trained machine learning model and publishes results to a central MQTT broker.

## Overview

The fog node client:
1. Downloads the fraud detection model and simulation data from an FTP server
2. Processes transactions locally using the Random Forest model
3. Publishes both raw transaction data and fraud predictions to MQTT topics
4. Sends email alerts when fraud is detected

---

## Prerequisites

- Network access to the FTP server (for downloading models)
- Network access to the MQTT broker (for publishing results)
- Gmail account for email alerts (optional)

---

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

### Step 1: Download Models and Data via FTP

Before running the fog node, you must download the required files from the FTP server:

#### Configure FTP Settings

Edit the FTP configuration in [`tests/test_FTP.py`](tests/test_FTP.py):

```python
FTP_HOST = "192.168.1.xxx"  # Change to your FTP server IP
FTP_USER = "fognode1"        # Change to your FTP username
FTP_PASS = "root"            # Change to your FTP password
LOCAL_ROOT = "."             # Local folder to save files (current directory)
```

#### Run FTP Download Script

```bash
python tests/test_FTP.py
```

This will download the following files to your local directory:
- `models/best_model_random_forest.pkl` - Trained Random Forest model
- `models/scaler.pkl` - Feature scaler
- `data/simulation_node_X.csv` - Simulation transaction data

**Note**: The FTP script recursively downloads all files and preserves the folder structure.

### Step 2: Configure Fog Node Settings

Edit the configuration variables in [`src/fog_node.py`](src/fog_node.py):

```python
# ---------- NODE CONFIGURATION ----------
NODE_ID = "Fog_Node_1"  # Change for each fog node (e.g., "Fog_Node_2", "Fog_Node_3")
MODEL_PATH = "models/best_model_random_forest.pkl"
SCALER_PATH = "models/scaler.pkl"
DATA_PATH = "data/simulation_node_1.csv"  # Change to match your node

# ---------- MQTT CONFIGURATION ----------
MQTT_BROKER = "192.168.1.xxx"  # Change to your MQTT broker IP
MQTT_PORT = 1883
TOPIC_RESULTS = "fog/transactions/results"
TOPIC_RAW = "fog/transactions/raw"
```

**Important**: Each fog node must have a **unique** `NODE_ID` and should use its corresponding simulation data file (e.g., `simulation_node_1.csv`, `simulation_node_2.csv`).

### Step 3: Configure Email Alerts (Optional)

Create a `.env` file in the client directory based on [`.env_exemple`](.env_exemple):

```bash
cp .env_exemple .env
```

Edit the `.env` file with your Gmail credentials:

```env
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "xxxx xxxx xxxx xxxx"  # Gmail App Password (not regular password)
RECEIVER_EMAIL = "alert-recipient@gmail.com"
```

> **Note**: For Gmail, you need to create an [App Password](https://support.google.com/accounts/answer/185833) rather than using your regular password. Enable 2-factor authentication first, then generate an app password.

---

## Usage

### Running the Fog Node

After downloading the models and configuring all settings:

```bash
python src/fog_node.py
```

### What Happens When Running

1. **Loads the model and scaler** from the `models/` directory
2. **Reads simulation data** from the configured CSV file
3. **Connects to MQTT broker** at the specified IP and port
4. **For each transaction**:
   - Scales the features using the pre-trained scaler
   - Makes a fraud prediction (0 = Legitimate, 1 = Fraud)
   - Publishes raw transaction data to `fog/transactions/raw`
   - Publishes prediction result to `fog/transactions/results`
   - **Sends email alert** if fraud is detected (Prediction = 1)
   - Waits 1 second before processing the next transaction

5. **Disconnects** after all transactions are processed

### Sample Output

```
[Fog_Node_1] Sent row 1 - Prediction = 0
[Fog_Node_1] Sent row 2 - Prediction = 1
Email sent successfully!
[Fog_Node_1] Sent row 3 - Prediction = 0
...
All data processed.
```

---

## MQTT Message Format

### Raw Transaction Message
Published to `fog/transactions/raw`:

```json
{
  "Node_ID": "Fog_Node_1",
  "Time": 70178,
  "V1": -0.443,
  "V2": 1.193,
  ...
  "V28": -0.072,
  "Amount": 11.99
}
```

### Fraud Prediction Message
Published to `fog/transactions/results`:

```json
{
  "Node_ID": "Fog_Node_1",
  "Time": 70178,
  "Prediction": 0
}
```

- **Prediction**: `0` = Legitimate transaction, `1` = Fraudulent transaction

---

## Testing Email Functionality

Before running the fog node, you can test if email alerts are working:

```bash
python tests/test_envoi_email.py
```

This will send a test email to verify your SMTP configuration.

---

## Directory Structure

```
client/
├── .env_exemple          # Example environment variables file
├── .gitignore           # Git ignore rules
├── requirements.txt     # Python dependencies
├── src/
│   └── fog_node.py     # Main fog node application
├── tests/
│   ├── test_FTP.py     # FTP download script
│   └── test_envoi_email.py  # Email test script
├── models/             # Downloaded ML models (created by FTP script)
│   ├── best_model_random_forest.pkl
│   └── scaler.pkl
└── data/               # Downloaded simulation data (created by FTP script)
    └── simulation_node_X.csv
```

---

## Troubleshooting

### FTP Download Issues

**Problem**: Cannot connect to FTP server

**Solutions**:
- Verify the FTP server is running (`src/ftp_server.py` on the server side)
- Check firewall settings allow FTP connections (port 21)
- Verify `FTP_HOST`, `FTP_USER`, and `FTP_PASS` are correct
- Ensure you're on the same network or the FTP server is accessible

### MQTT Connection Issues

**Problem**: Cannot connect to MQTT broker

**Solutions**:
- Verify the MQTT broker is running and accessible
- Check `MQTT_BROKER` IP address is correct
- Ensure port 1883 is open in firewall
- Test MQTT connectivity with tools like `mosquitto_sub`

### Email Sending Issues

**Problem**: Email alerts not sending

**Solutions**:
- Verify Gmail credentials in `.env` file
- Use an **App Password**, not your regular Gmail password
- Enable "Less secure app access" or use App Passwords (recommended)
- Check SMTP server and port (Gmail uses `smtp.gmail.com:587`)
- Verify internet connection

### Model Loading Issues

**Problem**: `FileNotFoundError` when loading model

**Solutions**:
- Ensure you ran `test_FTP.py` to download the models
- Verify paths in `MODEL_PATH`, `SCALER_PATH`, and `DATA_PATH`
- Check that `models/` and `data/` directories exist

### Data Processing Issues

**Problem**: Key errors or missing columns

**Solutions**:
- Ensure the CSV file contains all required features (V1-V28, Time, Amount, Class)
- Verify the data file matches the expected format
- Re-download the simulation data from the FTP server

---

## Running Multiple Fog Nodes

To simulate multiple fog nodes:

1. Copy the client folder to different machines or directories
2. For each instance, change:
   - `NODE_ID` to a unique identifier (e.g., "Fog_Node_1", "Fog_Node_2")
   - `DATA_PATH` to the corresponding simulation file
   - Keep the same `MQTT_BROKER` and `MQTT_PORT`
3. Run each instance separately

---

## Next Steps

After starting the fog node:

1. Monitor the console output for transaction processing
2. Check the server dashboard at `http://<server-ip>:8501` for real-time visualization
3. Verify transactions appear in the central database
4. Check email inbox for fraud alerts