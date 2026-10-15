# Configuration

## Variables to Change for Each Setup

### Server Side (`server/config.yaml`):
- `mqtt.broker.host` - MQTT broker IP address
- `mqtt.broker.port` - MQTT broker port (default: 1883)
- `database.path` - SQLite database location
- `fog_nodes` - List of expected fog nodes with IDs and names

### FTP Server (`server/src/ftp_server.py`, environment variables):
- `FTP_PASSWORD` - Password of the `fognode1`/`fognode2` FTP users (default: `root`)
- `FTP_PORT` - FTP port (default: 21)

### Client Side (`client/src/fog_node.py`, environment variables):
- `NODE_ID` - **Unique identifier for each fog node**
- `DATA_PATH` - Simulation data file path (match node ID)
- `MQTT_BROKER` - Server IP address running MQTT broker
- `MQTT_PORT` - MQTT broker port (default: 1883)
- `SEND_INTERVAL` - Seconds between transactions (default: 1)

### FTP Download (`client/src/download_models.py`, environment variables):
- `FTP_HOST` - Server IP address running FTP
- `FTP_USER` - FTP username
- `FTP_PASS` - FTP password

### Email Alerts (`client/.env`):
- `SENDER_EMAIL` - Gmail account for sending alerts
- `SENDER_PASSWORD` - Gmail App Password
- `RECEIVER_EMAIL` - Email address to receive fraud alerts
