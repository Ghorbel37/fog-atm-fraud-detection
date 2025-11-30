# ATM Fog Node Monitoring System - README

A real-time monitoring system for ATM fog nodes that collects transaction data and fraud detection results via MQTT and displays them on a Streamlit dashboard.

## System Components

1. **MQTT Subscriber** (`src/mqtt_subscriber.py`) - Connects to MQTT broker and listens to transaction and fraud result topics
2. **Database Handler** (`src/database.py`) - SQLite database for storing transactions, fraud results, and node status
3. **Streamlit Dashboard** (`src/dashboard.py`) - Real-time web dashboard for monitoring
4. **Configuration** (`config.yaml`) - MQTT broker settings and fog node definitions

## Quick Start

### 1. Install Dependencies

Activate your virtual environment and install required packages:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure the System

Use `config_example.yaml` as a template to create your own `config.yaml` file.
Edit `config.yaml` and fill in your values:

- **MQTT broker details** (host, port, username, password)
- **MQTT topics** for raw data and fraud results
- **Fog node information** (IDs, names, locations)

Initialize the SQLite db using this command:
```bash
.venv\Scripts\python.exe -c "from src.database import DatabaseHandler; db=DatabaseHandler();"
```

### 3. Start the MQTT Subscriber

The subscriber listens to MQTT topics and stores data in the database:

```bash
.venv\Scripts\python.exe src\mqtt_subscriber.py
```

Keep this running in the background.

### 4. Launch the Dashboard

In a new terminal, start the Streamlit dashboard:

```bash
.venv\Scripts\activate
streamlit run src\dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Testing with Sample Data

You can test the system with simulated data before connecting real fog nodes:

### Test Database Directly

```bash
.venv\Scripts\python.exe src\database.py
```

This creates a test database with sample data.

## Dashboard Features

- **Node Status Cards**: Real-time status of each fog node (online/offline/warning)
- **Transaction Feed**: Recent transactions from all nodes
- **Fraud Detection Results**: Color-coded fraud alerts with confidence scores
- **Analytics Charts**: 
  - Transaction volume over time
  - Fraud rate by node
- **Auto-refresh**: Configurable refresh interval for real-time updates

## File Structure

```
Fog Fraud detection/
├── config.yaml               # Configuration file (fill with your values)
├── requirements.txt          # Python dependencies
├── fog_monitoring.db         # SQLite database (auto-created)
├── src/
│   ├── database.py          # Database handler
│   ├── mqtt_subscriber.py   # MQTT client
│   ├── dashboard.py         # Streamlit dashboard
│   └── ftp_server.py        # FTP server used by the fog node the fetch the models
├── notebooks/               # Contains Jupyter notebooks for fetching the data and training the models
├── data/                    # Data files
├── models/                  # Model files
└── ftp_root/                # FTP directories
```

## Troubleshooting

**Dashboard shows "No transactions"?**
- Make sure MQTT subscriber is running
- Verify MQTT broker configuration in `config.yaml`
- Check that fog nodes are publishing to the correct topics
- Verify fog nodes name

**Nodes showing as offline?**
- Nodes must send data to update their status
- Check `node_offline_threshold` in `config.yaml`

**MQTT connection fails?**
- Verify broker host and port in `config.yaml`
- Check username/password credentials
- Ensure MQTT broker is running and accessible

## Next Steps

1. Fill in your actual MQTT broker details in `config.yaml`
2. Update fog node information (IDs, names, locations)
3. Initialize the SQLite db using this command:
```bash
.venv\Scripts\python.exe -c "from src.database import DatabaseHandler; db=DatabaseHandler();"
```
4. Configure your fog nodes to publish to the correct MQTT topics
5. Monitor your system in real-time via the dashboard!
