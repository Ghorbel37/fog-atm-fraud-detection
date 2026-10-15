# Manual setup

## Prerequisites

- **MQTT Broker** (e.g., Mosquitto)
- **Network connectivity** between server and fog nodes

## Part 1: Server Setup

### 1.1 Install Dependencies

Create a virtual environment in `server/` and install the dependencies into it:

```bash
cd server
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### 1.2 Prepare Dataset and Train Model

Run the Jupyter notebook to download the dataset, perform EDA, and train models
(in the same virtual environment, which gets the notebook extras):

```bash
pip install -r requirements-notebook.txt
jupyter notebook notebooks/credit_card_fraud_detection_complete.ipynb
```

**This notebook will**:
- Download the [Kaggle Credit Card Fraud Dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
- Perform exploratory data analysis
- Split data into train/test/simulation sets
- Train multiple ML models (Logistic Regression, Random Forest, XGBoost)
- Save the best model and scaler to `models/`

**Without Jupyter**: `python src/train.py` runs the same data split and trains the
selected Random Forest directly (downloads the dataset if needed, skips if the model
already exists; add `--force` to retrain).

**Output files**:
- `models/best_model_random_forest.pkl`
- `models/scaler.pkl`
- `data/simulation_node_1.csv`, `data/simulation_node_2.csv` (simulation data)

### 1.3 Configure Server

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

### 1.4 Initialize Database

```bash
python -c "from src.database import DatabaseHandler; db=DatabaseHandler(); print('Database initialized')"
```

### 1.5 Start Server Components

Open **three separate terminals**, activate the virtual environment in each one, and run:

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

## Part 2: Client (Fog Node) Setup

For each fog node (edge device):

### 2.1 Install Dependencies

Create a virtual environment in `client/` and install the dependencies into it:

```bash
cd client
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### 2.2 Download Models and Data from FTP Server

**Run the download script**, pointing it at your server with environment variables
(defaults: `FTP_HOST=192.168.1.158`, `FTP_USER=fognode1`, `FTP_PASS=root`):

```bash
FTP_HOST=192.168.1.xxx FTP_USER=fognode1 FTP_PASS=root python src/download_models.py
```

On Windows PowerShell, set the variables first (`$env:FTP_HOST="192.168.1.xxx"`), then run `python src/download_models.py`.

This downloads:
- `models/best_model_random_forest.pkl`
- `models/scaler.pkl`
- `data/simulation_node_X.csv`

### 2.3 Configure Fog Node

`src/fog_node.py` reads its settings from environment variables (they can also go in the `.env` file):

| Variable        | Default                               | Description                          |
| --------------- | ------------------------------------- | ------------------------------------ |
| `NODE_ID`       | `Fog_Node_1`                          | Unique name of this fog node         |
| `DATA_PATH`     | `data/simulation_node_1.csv`          | Simulation data for this node        |
| `MODEL_PATH`    | `models/best_model_random_forest.pkl` | Trained model                        |
| `SCALER_PATH`   | `models/scaler.pkl`                   | Fitted scaler                        |
| `MQTT_BROKER`   | `192.168.1.159`                       | IP/hostname of the MQTT broker       |
| `MQTT_PORT`     | `1883`                                | MQTT broker port                     |
| `SEND_INTERVAL` | `1`                                   | Seconds to wait between transactions |

> **Important**: Each fog node must have a **unique NODE_ID** and corresponding data file.

### 2.4 Configure Email Alerts (Optional)

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

### 2.5 Run Fog Node

```bash
NODE_ID=Fog_Node_1 DATA_PATH=data/simulation_node_1.csv MQTT_BROKER=192.168.1.xxx python src/fog_node.py
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

---

## Complete Workflow Summary

### Initial Setup (One-time)

1. **Server**: Download dataset from Kaggle
2. **Server**: Run EDA notebook to train models
3. **Server**: Configure `config.yaml`
4. **Server**: Initialize database
5. **Server**: Start FTP server, MQTT subscriber, dashboard

### For Each Fog Node

6. **Client**: Set `FTP_HOST`, `FTP_USER`, `FTP_PASS`
7. **Client**: Run `download_models.py` to download models and data
8. **Client**: Set a unique `NODE_ID`, its `DATA_PATH` and `MQTT_BROKER`
9. **Client**: (Optional) Configure email alerts in `.env`
10. **Client**: Run `fog_node.py`

### Monitoring

11. **Dashboard**: Open `http://localhost:8501` to monitor in real-time
12. **Email**: Receive fraud alerts when detected
