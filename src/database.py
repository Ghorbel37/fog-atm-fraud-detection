"""
Database handler for fog node monitoring system.
Manages SQLite database operations for fog nodes, transactions, and fraud results.
"""

import sqlite3
import json
import yaml
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import os


class DatabaseHandler:
    """Handles all database operations for the fog node monitoring system."""
    
    def __init__(self, db_path: str = None):
        """Initialize database handler with given database path."""
        if db_path is None:
            # Load from config.yaml
            db_path = self.load_db_path_from_config()
        self.db_path = db_path
        self.init_database()
    
    @staticmethod
    def load_db_path_from_config(config_path: str = "config.yaml") -> str:
        """Load database path from config file."""
        try:
            # Handle both absolute and relative paths
            if not os.path.isabs(config_path):
                # Look for config in project root (parent of src directory)
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(current_dir)
                config_path = os.path.join(project_root, config_path)
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config['database']['path']
        except Exception as e:
            print(f"Warning: Could not load database path from config: {e}")
            print("Using default: fog_monitoring.db")
            return "fog_monitoring.db"
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database and create tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Fog nodes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fog_nodes (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    location TEXT,
                    description TEXT,
                    node_string_id TEXT UNIQUE,
                    status TEXT DEFAULT 'offline',
                    last_seen TIMESTAMP,
                    created_at TIMESTAMP DEFAULT (DATETIME(CURRENT_TIMESTAMP, '+1 hour'))
                )
            """)
            
            # Transactions table - stores V1-V28 features, Time, Amount (Class removed)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id INTEGER NOT NULL,
                    time REAL,
                    v1 REAL, v2 REAL, v3 REAL, v4 REAL, v5 REAL,
                    v6 REAL, v7 REAL, v8 REAL, v9 REAL, v10 REAL,
                    v11 REAL, v12 REAL, v13 REAL, v14 REAL, v15 REAL,
                    v16 REAL, v17 REAL, v18 REAL, v19 REAL, v20 REAL,
                    v21 REAL, v22 REAL, v23 REAL, v24 REAL, v25 REAL,
                    v26 REAL, v27 REAL, v28 REAL,
                    amount REAL,
                    timestamp TIMESTAMP DEFAULT (DATETIME(CURRENT_TIMESTAMP, '+1 hour')),
                    FOREIGN KEY (node_id) REFERENCES fog_nodes(id)
                )
            """)
            
            # Fraud results table - stores Time and Prediction
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fraud_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id INTEGER,
                    node_id INTEGER NOT NULL,
                    time REAL,
                    prediction INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT (DATETIME(CURRENT_TIMESTAMP, '+1 hour')),
                    FOREIGN KEY (transaction_id) REFERENCES transactions(id),
                    FOREIGN KEY (node_id) REFERENCES fog_nodes(id)
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_node_id 
                ON transactions(node_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_timestamp 
                ON transactions(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fraud_results_node_id 
                ON fraud_results(node_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fraud_results_timestamp 
                ON fraud_results(timestamp)
            """)
    
    # Fog Nodes Operations
    
    def add_or_update_node(self, node_id: int, name: str, location: str = "", description: str = "", node_string_id: str = None):
        """Add a new fog node or update existing one."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO fog_nodes (id, name, location, description, node_string_id)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    location = excluded.location,
                    description = excluded.description,
                    node_string_id = excluded.node_string_id
            """, (node_id, name, location, description, node_string_id))
    
    def get_node_by_string_id(self, node_string_id: str):
        """Get a fog node by its string ID (e.g., 'Fog_Node_1')."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, location, description, node_string_id, status, last_seen, created_at
                FROM fog_nodes
                WHERE node_string_id = ?
            """, (node_string_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_node_status(self, node_id: int, status: str = "online"):
        """Update the status and last_seen timestamp of a fog node."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE fog_nodes 
                SET status = ?, last_seen = datetime('now', 'localtime')
                WHERE id = ?
            """, (status, node_id))
    
    def get_all_nodes(self) -> List[Dict]:
        """Get all fog nodes with their status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, location, description, status, last_seen, created_at
                FROM fog_nodes
                ORDER BY id
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_node_by_id(self, node_id: int) -> Optional[Dict]:
        """Get a specific fog node by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, location, description, status, last_seen, created_at
                FROM fog_nodes
                WHERE id = ?
            """, (node_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # Transactions Operations
    
    def add_transaction(self, node_id: int, transaction_data: Dict) -> int:
        """Add a new transaction with V1-V28 features (Class field removed)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Extract fields from transaction data
            fields = ['node_id', 'time']
            values = [node_id, transaction_data.get('Time')]
            
            # Add V1-V28 features
            for i in range(1, 29):
                fields.append(f'v{i}')
                values.append(transaction_data.get(f'V{i}'))
            
            # Add Amount (Class removed)
            fields.append('amount')
            values.append(transaction_data.get('Amount'))
            
            # Build SQL query
            placeholders = ', '.join(['?'] * len(fields))
            columns = ', '.join(fields)
            
            cursor.execute(f"""
                INSERT INTO transactions ({columns})
                VALUES ({placeholders})
            """, values)
            return cursor.lastrowid
    
    
    def get_recent_transactions(self, limit: int = 100, node_id: Optional[int] = None) -> List[Dict]:
        """Get recent transactions, optionally filtered by node."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if node_id is not None:
                cursor.execute("""
                    SELECT t.*, n.name as node_name
                    FROM transactions t
                    LEFT JOIN fog_nodes n ON t.node_id = n.id
                    WHERE t.node_id = ?
                    ORDER BY t.timestamp DESC
                    LIMIT ?
                """, (node_id, limit))
            else:
                cursor.execute("""
                    SELECT t.*, n.name as node_name
                    FROM transactions t
                    LEFT JOIN fog_nodes n ON t.node_id = n.id
                    ORDER BY t.timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_transaction_count(self, node_id: Optional[int] = None) -> int:
        """Get total transaction count, optionally for a specific node."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if node_id is not None:
                cursor.execute("SELECT COUNT(*) FROM transactions WHERE node_id = ?", (node_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM transactions")
            return cursor.fetchone()[0]
    
    
    # Fraud Results Operations
    
    def add_fraud_result(self, node_id: int, prediction: int, time: float = None, 
                        transaction_id: int = None) -> int:
        """Add a fraud detection result.
        
        Args:
            node_id: ID of the fog node
            prediction: 0 for legitimate, 1 for fraud
            time: Time value from fog node
            transaction_id: Optional ID of associated transaction
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO fraud_results (transaction_id, node_id, time, prediction)
                VALUES (?, ?, ?, ?)
            """, (transaction_id, node_id, time, prediction))
            return cursor.lastrowid
    
    
    def get_recent_fraud_results(self, limit: int = 100, node_id: Optional[int] = None) -> List[Dict]:
        """Get recent fraud results, optionally filtered by node."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if node_id is not None:
                cursor.execute("""
                    SELECT f.*, n.name as node_name
                    FROM fraud_results f
                    LEFT JOIN fog_nodes n ON f.node_id = n.id
                    WHERE f.node_id = ?
                    ORDER BY f.timestamp DESC
                    LIMIT ?
                """, (node_id, limit))
            else:
                cursor.execute("""
                    SELECT f.*, n.name as node_name
                    FROM fraud_results f
                    LEFT JOIN fog_nodes n ON f.node_id = n.id
                    ORDER BY f.timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    
    def get_fraud_stats(self, node_id: Optional[int] = None) -> Dict:
        """Get fraud statistics, optionally for a specific node."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if node_id is not None:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) as fraud_count
                    FROM fraud_results
                    WHERE node_id = ?
                """, (node_id,))
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) as fraud_count
                    FROM fraud_results
                """)
            
            row = cursor.fetchone()
            data = dict(row)
            data['fraud_rate'] = (data['fraud_count'] / data['total'] * 100) if data['total'] > 0 else 0
            return data


if __name__ == "__main__":
    # Test database operations
    db = DatabaseHandler("test_fog_monitoring.db")
    
    # Add test nodes
    db.add_or_update_node(1, "Fog Node 1", "Location A", "Test node 1")
    db.add_or_update_node(2, "Fog Node 2", "Location B", "Test node 2")
    
    # Test transaction
    tx_id = db.add_transaction(1, {"amount": 100.50, "type": "payment"})
    print(f"Added transaction with ID: {tx_id}")
    
    # Test fraud result
    fraud_id = db.add_fraud_result(1, True, 0.95, tx_id)
    print(f"Added fraud result with ID: {fraud_id}")
    
    # Update node status
    db.update_node_status(1, "online")
    
    # Get all nodes
    nodes = db.get_all_nodes()
    print(f"\nAll nodes: {nodes}")
    
    # Get stats
    stats = db.get_fraud_stats()
    print(f"\nFraud stats: {stats}")
    
    print("\nDatabase operations test completed successfully!")
