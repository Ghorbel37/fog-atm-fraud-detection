"""
MQTT Subscriber for fog node monitoring system.
Listens to MQTT topics for transaction data and fraud results, stores in database.
"""

import paho.mqtt.client as mqtt
import yaml
import json
import logging
from datetime import datetime
from database import DatabaseHandler


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MQTTSubscriber:
    """MQTT subscriber that processes messages and stores them in the database."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize MQTT subscriber with configuration."""
        self.config = self.load_config(config_path)
        self.db = DatabaseHandler(self.config['database']['path'])
        self.client = None
        
        # Initialize fog nodes in database from config
        self.init_fog_nodes()
        
    def load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def init_fog_nodes(self):
        """Initialize fog nodes in database from configuration."""
        for node in self.config['fog_nodes']:
            # Create node_string_id from node name (e.g., "Fog Node 1" -> "Fog_Node_1")
            node_string_id = node['name'].replace(' ', '_')
            self.db.add_or_update_node(
                node['id'],
                node['name'],
                node.get('location', ''),
                node.get('description', ''),
                node_string_id
            )
        logger.info(f"Initialized {len(self.config['fog_nodes'])} fog nodes in database")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            
            # Subscribe to topics
            raw_data_topic = self.config['mqtt']['topics']['raw_data']
            fraud_results_topic = self.config['mqtt']['topics']['fraud_results']
            
            client.subscribe(raw_data_topic)
            client.subscribe(fraud_results_topic)
            
            logger.info(f"Subscribed to topic: {raw_data_topic}")
            logger.info(f"Subscribed to topic: {fraud_results_topic}")
        else:
            logger.error(f"Connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker (code {rc})")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def on_message(self, client, userdata, msg):
        """Callback when a message is received."""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            logger.debug(f"Received message on topic '{topic}': {payload}")
            
            # Extract Node_ID from payload (string format like "Fog_Node_1")
            node_string_id = payload.get('Node_ID')
            
            if not node_string_id:
                logger.warning(f"No Node_ID in payload from topic '{topic}', skipping message")
                return
            
            # Map string node_id to numeric id
            node = self.db.get_node_by_string_id(node_string_id)
            if not node:
                logger.warning(f"Unknown Node_ID '{node_string_id}', skipping message")
                return
            
            node_id = node['id']

            # Determine which topic type the message came from
            if 'raw' in topic:
                self.handle_raw_data(payload, node_id)
            elif 'results' in topic:
                self.handle_fraud_result(payload, node_id)
            else:
                logger.warning(f"Received message from unknown topic: {topic}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    
    def handle_raw_data(self, payload: dict, node_id: int):
        """Handle raw transaction data message.
        
        Expected format:
        {'Time': 70178, 'V1': -0.443, ..., 'V28': -0.072, 'Amount': 11.99, 'Node_ID': 'Fog_Node_1'}
        Note: Class field has been removed from the data
        """
        try:
            # Payload has all the V1-V28 features, Time, Amount (Class removed)
            # Just pass it directly to the database
            tx_id = self.db.add_transaction(node_id, payload)
            
            # Update node status to online
            self.db.update_node_status(node_id, 'online')
            
            amount = payload.get('Amount', 'N/A')
            time = payload.get('Time', 'N/A')
            node_string_id = payload.get('Node_ID', 'N/A')
            logger.info(f"Added transaction {tx_id} from {node_string_id} (node_id={node_id}, Amount: {amount}, Time: {time})")
            
        except Exception as e:
            logger.error(f"Error handling raw data: {e}")
    
    
    def handle_fraud_result(self, payload: dict, node_id: int):
        """Handle fraud detection result message.
        
        Expected format:
        {'Node_ID': 'Fog_Node_1', 'Time': 70178, 'Prediction': 0}  # 0 = legitimate, 1 = fraud
        """
        try:
            time = payload.get('Time')
            prediction = payload.get('Prediction', 0)
            node_string_id = payload.get('Node_ID', 'N/A')
            
            # Add fraud result to database
            fraud_id = self.db.add_fraud_result(
                node_id=node_id,
                prediction=prediction,
                time=time
            )
            
            # Update node status to online
            self.db.update_node_status(node_id, 'online')
            
            fraud_status = "FRAUD" if prediction == 1 else "LEGITIMATE"
            logger.info(f"Added fraud result {fraud_id} from {node_string_id} (node_id={node_id}): {fraud_status} (Time: {time})")
            
        except Exception as e:
            logger.error(f"Error handling fraud result: {e}")
    
    def connect(self):
        """Connect to MQTT broker and start listening."""
        try:
            mqtt_config = self.config['mqtt']['broker']
            
            # Create MQTT client
            self.client = mqtt.Client()
            
            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            # Set username and password if provided
            if mqtt_config.get('username') and mqtt_config.get('password'):
                self.client.username_pw_set(
                    mqtt_config['username'],
                    mqtt_config['password']
                )
            
            # Connect to broker
            logger.info(f"Connecting to MQTT broker at {mqtt_config['host']}:{mqtt_config['port']}")
            self.client.connect(
                mqtt_config['host'],
                mqtt_config['port'],
                mqtt_config.get('keepalive', 60)
            )
            
            # Start the loop
            logger.info("Starting MQTT client loop...")
            self.client.loop_forever()
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.client:
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")


def main():
    """Main function to run the MQTT subscriber."""
    import sys
    
    config_path = "config.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    logger.info("Starting MQTT Subscriber for Fog Node Monitoring System")
    logger.info(f"Using configuration file: {config_path}")
    
    subscriber = MQTTSubscriber(config_path)
    
    try:
        subscriber.connect()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        subscriber.disconnect()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
