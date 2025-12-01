# Fog Node Fraud Detection System

A distributed real-time credit card fraud detection system using fog computing architecture. The system employs machine learning models deployed at the edge (fog nodes) with centralized monitoring via MQTT and a Streamlit dashboard.

## System Overview

This project implements a complete fraud detection pipeline:
1. **Data Preparation** - Download and process Kaggle credit card fraud dataset
2. **Model Training** - Train and evaluate multiple ML models, select best performer
3. **Model Distribution** - Deploy models to fog nodes via FTP server
4. **Edge Processing** - Fog nodes perform fraud detection locally
5. **Real-time Monitoring** - Centralized dashboard tracks all transactions and predictions
---

## Data Preparation

### Dataset

**Source**: [Kaggle Credit Card Fraud Detection Dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)

**Dataset Details**:
- File: `data/creditcard.csv` (150MB)
- Records: 284,807 credit card transactions
- Features: 28 PCA-transformed features (V1-V28) + Time + Amount
- Target: Class (0 = Legitimate, 1 = Fraud)
- Imbalance: ~0.17% fraud cases

### Data Splits

After EDA and processing, the dataset is split into:

| File                    | Size  | Purpose               |
| ----------------------- | ----- | --------------------- |
| `train_data.csv`        | 119MB | Model training        |
| `test_data.csv`         | 30MB  | Model evaluation      |
| `simulation_node_1.csv` | 1MB   | Fog Node 1 simulation |
| `simulation_node_2.csv` | 1MB   | Fog Node 2 simulation |

### Exploratory Data Analysis

Performed in `notebooks/credit_card_fraud_detection_complete.ipynb`:
- Class distribution analysis
- Feature correlation studies
- Temporal patterns
- Amount distribution by class
- Statistical summaries

---

## Model Training

### Training Process

The training notebook evaluates multiple models:
- Logistic Regression
- **Random Forest Classifier** **(Selected)**
- XGBoost
- Neural Networks

**Evaluation Metrics**:
- Precision, Recall, F1-Score
- ROC-AUC
- Confusion Matrix
- Handling class imbalance (SMOTE/class weights)

### Trained Artifacts

| File                                  | Size | Description                              |
| ------------------------------------- | ---- | ---------------------------------------- |
| `models/best_model_random_forest.pkl` | 17MB | Trained Random Forest classifier         |
| `models/scaler.pkl`                   | 2KB  | StandardScaler for feature normalization |

**Model Performance**: Optimized for high recall to minimize false negatives (missed frauds) while maintaining acceptable precision.

---

## System Architecture

### Components

1. **FTP Server** (`src/ftp_server.py`)
   - Distributes models and simulation data to fog nodes
   - Port: 21
   - Root: `ftp_root/` directory

2. **MQTT Broker**
   - Message broker for real-time communication
   - Topics: `fog/transactions/raw`, `fog/transactions/results`

3. **MQTT Subscriber** (`src/mqtt_subscriber.py`)
   - Receives messages from fog nodes
   - Stores data in SQLite database
   - Tracks node status

4. **SQLite Database** (`fog_monitoring.db`)
   - Tables: fog_nodes, transactions, fraud_results
   - Stores V1-V28 features, Amount, Time, Predictions

5. **Streamlit Dashboard** (`src/dashboard.py`)
   - Real-time visualization
   - Node status monitoring
   - Transaction and fraud analytics

6. **Fog Nodes** (Clients)
   - Fetch models from FTP
   - Process transactions locally
   - Publish results to MQTT

---

## Quick Start

### Prerequisites

```bash
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 1. Data Preparation & Model Training

```bash
# Run Jupyter notebook for complete workflow
jupyter notebook notebooks/credit_card_fraud_detection_complete.ipynb
```

This notebook will:
- Download creditcard.csv dataset
- Perform EDA
- Split data into train/test/simulation sets
- Train multiple models
- Save best model and scaler to `models/`

### 2. Configure the System

Edit `config.yaml` (use `config_example.yaml` as template):

```yaml
mqtt:
  broker:
    host: "localhost"      # Your MQTT broker
    port: 1883
    username: ""           # Optional
    password: ""           # Optional
  topics:
    raw_data: "fog/transactions/raw"
    fraud_results: "fog/transactions/results"

database:
  path: "fog_monitoring.db"

fog_nodes:
  - id: 1
    name: "Fog Node 1"
    location: "ATM Location A"
  - id: 2
    name: "Fog Node 2"
    location: "ATM Location B"
```

### 3. Initialize Database

```bash
.venv\Scripts\python.exe -c "from src.database import DatabaseHandler; db=DatabaseHandler(); print('Database initialized')"
```

### 4. Start Server Infrastructure

**Terminal 1 - FTP Server**:
```bash
.venv\Scripts\python.exe src\ftp_server.py
```

**Terminal 2 - MQTT Subscriber**:
```bash
.venv\Scripts\python.exe src\mqtt_subscriber.py
```

**Terminal 3 - Dashboard**:
```bash
streamlit run src\dashboard.py
```

Dashboard will open at `http://localhost:8501`

### 5. Launch Fog Nodes

On each fog node client:
1. Connect to FTP server and download:
   - `best_model_random_forest.pkl`
   - `scaler.pkl`
   - `simulation_node_X.csv`
2. Configure MQTT connection
3. Start processing and publishing transactions

---

## MQTT Message Format

### Raw Transaction (Published by Fog Node)
```json
{
  "Node_ID": "Fog_Node_1",
  "Time": 70178,
  "V1": -0.443, "V2": 1.193, ..., "V28": -0.072,
  "Amount": 11.99
}
```

### Fraud Result (Published by Fog Node)
```json
{
  "Node_ID": "Fog_Node_1",
  "Time": 70178,
  "Prediction": 0
}
```
- **Prediction**: `0` = Legitimate, `1` = Fraud

---

## Testing with Sample Data

You can test the system with simulated data before connecting real fog nodes:

### Test Database Directly

```bash
.venv\Scripts\python.exe src\database.py
```

This creates a test database with sample data.

## Dashboard Features

Access the dashboard at `http://localhost:8501`

**Real-time Monitoring**:
- **Node Status Cards**: Visual indicators (🟢 Online, 🟠 Warning, 🔴 Offline, ⚪ Unknown)
- **Last Seen Timestamps**: Track when each node last communicated
- **Auto-refresh**: Configurable refresh interval (default: 5 seconds)

**Transaction Feed**:
- Recent 20 transactions displayed in table format
- Shows: ID, Node, Time, Amount, Timestamp
- Real-time updates as fog nodes publish data

**Fraud Detection Results**:
- Color-coded fraud alerts (🟢 Legitimate, 🔴 Fraud)
- Prediction confidence
- Time correlation with transactions

**Analytics Charts**:
- **Transaction Volume Over Time**: Hourly transaction counts (line chart)
- **Transaction Amount Distribution**: Histogram of transaction amounts
- **Fraud Rate by Node**: Bar chart showing fraud percentage per node

**Filtering**:
- Filter by specific fog node
- View all nodes combined

---

## File Structure

```
Fog Fraud detection/
├── config.yaml               # Configuration file (fill with your values)
├── config_example.yaml      # Configuration template│
├── requirements.txt          # Python dependencies
├── fog_monitoring.db         # SQLite database (auto-created)
├── src/
│   ├── database.py          # SQLite database handler
│   ├── mqtt_subscriber.py   # MQTT client for receiving data
│   ├── dashboard.py         # Streamlit dashboard
│   └── ftp_server.py        # FTP server used by the fog node the fetch the models
├── notebooks/               # Jupyter notebooks
│   └── credit_card_fraud_detection_complete.ipynb  # Full training pipeline
├── data/                    # Dataset files
├── models/                  # Trained model artifacts
└── ftp_root/                # FTP server directories
```

---

## Troubleshooting

**Dashboard shows "No transactions"?**
- Ensure MQTT subscriber is running (`src/mqtt_subscriber.py`)
- Verify MQTT broker configuration in `config.yaml`
- Check that fog nodes are publishing to the correct topics
- Verify fog nodes name

**Nodes showing as offline?**
- Nodes must send data to update their status
- Check `node_offline_threshold` in `config.yaml`
- Verify fog nodes are actively publishing messages

**MQTT connection fails?**
- Verify broker host and port in `config.yaml`
- Check username/password credentials
- Ensure MQTT broker is running and accessible

**Database errors?**
- Delete `fog_monitoring.db` and reinitialize
- Verify database path in `config.yaml`
- Check file permissions

**FTP connection issues?**
- Ensure FTP server is running on port 21
- Verify firewall allows FTP connections
- Check FTP credentials in fog node configuration

---

## Development & Testing

### Test Database Directly
```bash
.venv\Scripts\python.exe src\database.py
```
---

## Project Workflow Summary

1. **Download Dataset** → Download `creditcard.csv` from Kaggle
2. **Run EDA Notebook** → Explore data, identify patterns
3. **Train Models** → Compare multiple algorithms, select Random Forest
4. **Split Data** → Create training, testing, and simulation sets
5. **Start FTP Server** → Distribute models to fog nodes
6. **Configure MQTT** → Set up broker and topics
7. **Initialize Database** → Create SQLite schema
8. **Start Subscriber** → Listen for MQTT messages
9. **Launch Dashboard** → Monitor real-time fraud detection
10. **Deploy Fog Nodes** → Edge devices process transactions locally