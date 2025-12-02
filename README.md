# Fog ATM Fraud Detection System

A distributed real-time credit card fraud detection system using fog computing architecture. The system employs machine learning models deployed at the edge (fog nodes) with centralized monitoring via MQTT and a Streamlit dashboard.

## Project Overview

This project implements a complete end-to-end fraud detection pipeline with fog computing:

1. **Data Preparation** - Download and process Kaggle credit card fraud dataset
2. **Model Training** - Train and evaluate multiple ML models, select best performer
3. **Model Distribution** - Deploy models to fog nodes via FTP server
4. **Edge Processing** - Fog nodes perform fraud detection locally at edge devices
5. **Real-time Monitoring** - Centralized dashboard tracks all transactions and fraud predictions
6. **Alert System** - Email notifications when fraud is detected

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         SERVER SIDE                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  FTP Server  │  │ MQTT Broker  │  │  MQTT Subscriber     │  │
│  │  (Port 21)   │  │  (Port 1883) │  │  (Stores to DB)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│         │                  ▲                      │              │
│         │                  │                      ▼              │
│    ┌────────┐         ┌────────┐         ┌──────────────┐      │
│    │ Models │         │ Topics │         │   SQLite DB  │      │
│    │  Data  │         │        │         │              │      │
│    └────────┘         └────────┘         └──────────────┘      │
│                                                    │              │
│                                           ┌──────────────────┐  │
│                                           │  Dashboard       │  │
│                                           │  (Streamlit)     │  │
│                                           └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ MQTT Messages
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                            │
┌───────▼──────────┐                     ┌──────────▼─────────┐
│  CLIENT SIDE 1   │                     │  CLIENT SIDE 2     │
│  ┌────────────┐  │                     │  ┌────────────┐    │
│  │ Fog Node 1 │  │                     │  │ Fog Node 2 │    │
│  │            │  │  ...                │  │            │    │
│  │ + ML Model │  │                     │  │ + ML Model │    │
│  │ + Data     │  │                     │  │ + Data     │    │
│  └────────────┘  │                     │  └────────────┘    │
└──────────────────┘                     └────────────────────┘
```

## Project Structure

```
fog-atm-fraud-detection/
├── README.md                     # This file - Project overview
├── client/                       # FOG NODE (Edge devices)
│   ├── README.md                # Client-specific setup instructions
│   ├── .env_exemple             # Email configuration template
│   ├── requirements.txt         # Client dependencies
│   ├── src/
│   │   └── fog_node.py         # Main fog node application
│   ├── tests/
│   │   ├── test_FTP.py         # Download models from FTP server
│   │   └── test_envoi_email.py # Test email alerts
│   ├── models/                  # Downloaded ML models (via FTP)
│   └── data/                    # Downloaded simulation data (via FTP)
│
└── server/                       # CENTRAL SERVER
    ├── README.md                # Server-specific documentation
    ├── config.yaml              # Server configuration
    ├── config_example.yaml      # Configuration template
    ├── requirements.txt         # Server dependencies
    ├── src/
    │   ├── ftp_server.py       # FTP server for model distribution
    │   ├── mqtt_subscriber.py  # MQTT client receiving fog node data
    │   ├── dashboard.py        # Streamlit monitoring dashboard
    │   └── database.py         # SQLite database handler
    ├── notebooks/
    │   └── credit_card_fraud_detection_complete.ipynb
    ├── data/                    # Dataset and splits
    ├── models/                  # Trained models
    └── ftp_root/                # FTP server root directory
```

---

## Quick Start Guide

### Prerequisites

- **MQTT Broker** (e.g., Mosquitto)
- **Network connectivity** between server and fog nodes

### Part 1: Server Setup

#### 1.1 Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

#### 1.2 Prepare Dataset and Train Model

Run the Jupyter notebook to download the dataset, perform EDA, and train models:

```bash
jupyter notebook notebooks/credit_card_fraud_detection_complete.ipynb
```

**This notebook will**:
- Download the [Kaggle Credit Card Fraud Dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
- Perform exploratory data analysis
- Split data into train/test/simulation sets
- Train multiple ML models (Logistic Regression, Random Forest, XGBoost)
- Save the best model and scaler to `models/`

**Output files**:
- `models/best_model_random_forest.pkl`
- `models/scaler.pkl`
- `data/simulation_node_1.csv`, `data/simulation_node_2.csv` (simulation data)

#### 1.3 Configure Server

Copy the example configuration and edit it:

```bash
cp config_example.yaml config.yaml
```

Edit `config.yaml` with your settings:

```yaml
mqtt:
  broker:
    host: "localhost"      # Your MQTT broker IP
    port: 1883
  topics:
    raw_data: "fog/transactions/raw"
    fraud_results: "fog/transactions/results"

database:
  path: "fog_monitoring.db"

fog_nodes:
  - id: 1
    name: "Fog_Node_1"
    location: "ATM Location A"
  - id: 2
    name: "Fog_Node_2"
    location: "ATM Location B"
```

#### 1.4 Initialize Database

```bash
python -c "from src.database import DatabaseHandler; db=DatabaseHandler(); print('Database initialized')"
```

#### 1.5 Start Server Components

Open **three separate terminals** and run:

**Terminal 1 - FTP Server**:
```bash
cd server
python src/ftp_server.py
```

**Terminal 2 - MQTT Subscriber**:
```bash
cd server
python src/mqtt_subscriber.py
```

**Terminal 3 - Dashboard**:
```bash
cd server
streamlit run src/dashboard.py
```

The dashboard will be available at: **http://localhost:8501**

---

### Part 2: Client (Fog Node) Setup

For each fog node (edge device):

#### 2.1 Install Dependencies

```bash
cd client
pip install -r requirements.txt
```

#### 2.2 Download Models and Data from FTP Server

**Configure FTP settings** in `tests/test_FTP.py`:

```python
FTP_HOST = "192.168.1.xxx"  # Change to your server IP
FTP_USER = "fognode1"        # Change to your FTP username
FTP_PASS = "root"            # Change to your FTP password
```

**Run the download script**:

```bash
python tests/test_FTP.py
```

This downloads:
- `models/best_model_random_forest.pkl`
- `models/scaler.pkl`
- `data/simulation_node_X.csv`

#### 2.3 Configure Fog Node

Edit `src/fog_node.py` configuration:

```python
# ---------- CONFIGURATION ----------
NODE_ID = "Fog_Node_1"  # CHANGE FOR EACH NODE (Fog_Node_1, Fog_Node_2, etc.)
MODEL_PATH = "models/best_model_random_forest.pkl"
SCALER_PATH = "models/scaler.pkl"
DATA_PATH = "data/simulation_node_1.csv"  # CHANGE for each node

MQTT_BROKER = "192.168.1.xxx"  # CHANGE to your server IP
MQTT_PORT = 1883
```

> **Important**: Each fog node must have a **unique NODE_ID** and corresponding data file.

#### 2.4 Configure Email Alerts (Optional)

Create `.env` file from template:

```bash
cp .env_exemple .env
```

Edit `.env` with Gmail credentials:

```env
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "xxxx xxxx xxxx xxxx"  # Gmail App Password
RECEIVER_EMAIL = "alert-recipient@gmail.com"
```

> **Note**: Use a Gmail [App Password](https://support.google.com/accounts/answer/185833), not your regular password.

#### 2.5 Run Fog Node

```bash
python src/fog_node.py
```

**Expected output**:
```
[Fog_Node_1] Sent row 1 - Prediction = 0
[Fog_Node_1] Sent row 2 - Prediction = 1
Email sent successfully!
[Fog_Node_1] Sent row 3 - Prediction = 0
...
All data processed.
```

---

## Dataset Information

**Source**: [Kaggle Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)

**Details**:
- **Size**: 150MB
- **Records**: 284,807 transactions
- **Features**: 28 PCA-transformed features (V1-V28) + Time + Amount
- **Target**: Class (0 = Legitimate, 1 = Fraud)
- **Imbalance**: ~0.17% fraud cases

---

## Machine Learning Models

**Trained Models**:
- Logistic Regression
- **Random Forest Classifier** **(Selected)**
- XGBoost
- Neural Networks

**Evaluation Metrics**:
- Precision, Recall, F1-Score
- ROC-AUC
- Confusion Matrix
- Class imbalance handling (SMOTE/class weights)

**Model Files**:
- `models/best_model_random_forest.pkl` - Trained classifier
- `models/scaler.pkl` - StandardScaler for normalization

**Performance**: Optimized for high recall to minimize false negatives (missed frauds).

---

## MQTT Communication

### Topics

- **`fog/transactions/raw`** - Raw transaction data from fog nodes
- **`fog/transactions/results`** - Fraud prediction results from fog nodes

### Message Formats

**Raw Transaction** (published by fog node):
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

**Fraud Result** (published by fog node):
```json
{
  "Node_ID": "Fog_Node_1",
  "Time": 70178,
  "Prediction": 0
}
```

- **Prediction**: `0` = Legitimate, `1` = Fraudulent

---

## Dashboard Features

Access at **http://localhost:8501**

**Real-time Monitoring**:
- 🟢 Online / 🟠 Warning / 🔴 Offline / ⚪ Unknown node status
- Last seen timestamps
- Auto-refresh (configurable interval)

**Visualizations**:
- **Recent Transactions** - Last 20 transactions table
- **Fraud Alerts** - Color-coded fraud detection results
- **Transaction Volume Over Time** - Hourly line chart
- **Amount Distribution** - Histogram
- **Fraud Rate by Node** - Bar chart comparison

**Filtering**:
- Filter by specific fog node
- View all nodes combined

---

## Configuration Summary

### Variables to Change for Each Setup

#### Server Side (`server/config.yaml`):
- `mqtt.broker.host` - MQTT broker IP address
- `mqtt.broker.port` - MQTT broker port (default: 1883)
- `database.path` - SQLite database location
- `fog_nodes` - List of expected fog nodes with IDs and names

#### Client Side (`client/src/fog_node.py`):
- `NODE_ID` - **Unique identifier for each fog node**
- `DATA_PATH` - Simulation data file path (match node ID)
- `MQTT_BROKER` - Server IP address running MQTT broker
- `MQTT_PORT` - MQTT broker port (default: 1883)

#### FTP Download (`client/tests/test_FTP.py`):
- `FTP_HOST` - Server IP address running FTP
- `FTP_USER` - FTP username
- `FTP_PASS` - FTP password

#### Email Alerts (`client/.env`):
- `SENDER_EMAIL` - Gmail account for sending alerts
- `SENDER_PASSWORD` - Gmail App Password
- `RECEIVER_EMAIL` - Email address to receive fraud alerts

---

## Troubleshooting

### Server Issues

**Dashboard shows "No transactions"?**
- Verify MQTT subscriber is running
- Check MQTT broker configuration in `config.yaml`
- Ensure fog nodes are publishing to correct topics
- Verify fog node names match `config.yaml`

**Nodes showing as offline?**
- Nodes must send data to update status
- Check `node_offline_threshold` in `config.yaml`
- Verify fog nodes are actively publishing

**MQTT connection fails?**
- Verify broker host/port in `config.yaml`
- Check MQTT broker is running and accessible
- Test with `mosquitto_sub -h <host> -t "#"`

**Database errors?**
- Delete `fog_monitoring.db` and reinitialize
- Check file permissions
- Verify database path in `config.yaml`

**FTP server issues?**
- Ensure FTP server is running on port 21
- Check firewall allows FTP connections
- Verify `ftp_root/` directory exists

### Client Issues

**FTP download fails?**
- Verify FTP server is running on server side
- Check `FTP_HOST`, `FTP_USER`, `FTP_PASS` in `test_FTP.py`
- Ensure network connectivity to server
- Check firewall allows FTP (port 21)

**MQTT connection fails?**
- Verify `MQTT_BROKER` IP is correct
- Ensure MQTT broker is running and accessible
- Check firewall allows port 1883
- Test connectivity: `ping <MQTT_BROKER>`

**Email alerts not working?**
- Use Gmail App Password, not regular password
- Verify credentials in `.env` file
- Check SMTP settings (`smtp.gmail.com:587`)
- Test with `python tests/test_envoi_email.py`

**Model loading errors?**
- Ensure `test_FTP.py` was run successfully
- Verify `models/` directory contains `.pkl` files
- Check file paths in `fog_node.py`

---

## Complete Workflow Summary

### Initial Setup (One-time)

1. **Server**: Download dataset from Kaggle
2. **Server**: Run EDA notebook to train models
3. **Server**: Configure `config.yaml`
4. **Server**: Initialize database
5. **Server**: Start FTP server, MQTT subscriber, dashboard

### For Each Fog Node

6. **Client**: Configure FTP settings in `test_FTP.py`
7. **Client**: Run `test_FTP.py` to download models and data
8. **Client**: Configure unique `NODE_ID` and `MQTT_BROKER` in `fog_node.py`
9. **Client**: (Optional) Configure email alerts in `.env`
10. **Client**: Run `fog_node.py`

### Monitoring

11. **Dashboard**: Open `http://localhost:8501` to monitor in real-time
12. **Email**: Receive fraud alerts when detected

---

## System Workflow

```
1. Fog Node downloads model & data via FTP
         ↓
2. Fog Node loads ML model locally
         ↓
3. Fog Node processes transactions (edge computing)
         ↓
4. Fog Node publishes raw data → MQTT → Server
         ↓
5. Fog Node publishes predictions → MQTT → Server
         ↓
6. MQTT Subscriber saves to SQLite database
         ↓
7. Dashboard visualizes real-time data
         ↓
8. Email alerts sent on fraud detection
```

---

## Additional Resources

- **Server Documentation**: See [`server/README.md`](server/README.md)
- **Client Documentation**: See [`client/README.md`](client/README.md)
- **Training Notebook**: `server/notebooks/credit_card_fraud_detection_complete.ipynb`

---

## Running Multiple Fog Nodes

To simulate multiple fog nodes:

1. **Option A - Different Machines**:
   - Install client on each machine
   - Use unique `NODE_ID` for each
   - Point all to same `MQTT_BROKER`

2. **Option B - Same Machine**:
   - Copy client folder to multiple directories
   - Configure each with unique `NODE_ID`
   - Use different simulation data files
   - Run each in separate terminal

**Example**:
```bash
# Terminal 1
cd client_node1
NODE_ID="Fog_Node_1" DATA_PATH="data/simulation_node_1.csv" python src/fog_node.py

# Terminal 2
cd client_node2
NODE_ID="Fog_Node_2" DATA_PATH="data/simulation_node_2.csv" python src/fog_node.py
```