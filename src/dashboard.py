"""
Streamlit Dashboard for Fog Node Monitoring System.
Displays real-time status of fog nodes, transaction data, and fraud detection results.
"""

import streamlit as st
import pandas as pd
import yaml
from datetime import datetime, timedelta
import time
from database import DatabaseHandler
import plotly.express as px
import plotly.graph_objects as go


# Page configuration
st.set_page_config(
    page_title="Fog Node Monitoring Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def load_config():
    """Load configuration from YAML file."""
    with open("config.yaml", 'r') as f:
        return yaml.safe_load(f)


@st.cache_resource
def get_db():
    """Get database handler instance."""
    config = load_config()
    return DatabaseHandler(config['database']['path'])


def get_node_status_color(node):
    """Determine status color based on last seen time."""
    config = load_config()
    offline_threshold = config['dashboard']['node_offline_threshold']
    
    if not node['last_seen']:
        return 'gray', 'unknown'
    
    last_seen = datetime.fromisoformat(node['last_seen'])
    time_diff = (datetime.now() - last_seen).total_seconds()
    
    if time_diff < offline_threshold:
        return 'green', 'online'
    elif time_diff < offline_threshold * 3:
        return 'orange', 'warning'
    else:
        return 'red', 'offline'


def format_timestamp(timestamp_str):
    """Format timestamp for display."""
    if not timestamp_str:
        return "Never"
    
    try:
        dt = datetime.fromisoformat(timestamp_str)
        time_diff = datetime.now() - dt
        
        if time_diff < timedelta(seconds=60):
            return f"{int(time_diff.total_seconds())}s ago"
        elif time_diff < timedelta(hours=1):
            return f"{int(time_diff.total_seconds() / 60)}m ago"
        elif time_diff < timedelta(days=1):
            return f"{int(time_diff.total_seconds() / 3600)}h ago"
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str


def render_node_card(node, stats):
    """Render a single fog node status card."""
    color, status = get_node_status_color(node)
    
    # Status indicator emoji
    status_emoji = {
        'online': '🟢',
        'warning': '🟠',
        'offline': '🔴',
        'unknown': '⚪'
    }
    
    with st.container():
        st.markdown(f"""
        <div style="
            border: 2px solid {color};
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            background-color: rgba(0,0,0,0.05);
        ">
            <h3>{status_emoji[status]} {node['name']}</h3>
            <p><strong>ID:</strong> {node['id']}</p>
            <p><strong>Location:</strong> {node['location'] or 'N/A'}</p>
            <p><strong>Status:</strong> {status.upper()}</p>
            <p><strong>Last Seen:</strong> {format_timestamp(node['last_seen'])}</p>
            <p><strong>Transactions:</strong> {stats['total_tx']}</p>
            <p><strong>Fraud Rate:</strong> {stats['fraud_rate']:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main dashboard function."""
    
    # Title
    st.title("🌐 Fog Node Monitoring Dashboard")
    st.markdown("---")
    
    # Get database connection
    db = get_db()
    config = load_config()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Auto refresh
        auto_refresh = st.checkbox("Auto Refresh", value=True)
        refresh_interval = st.slider(
            "Refresh Interval (seconds)",
            min_value=1,
            max_value=30,
            value=config['dashboard']['refresh_interval']
        )
        
        st.markdown("---")
        
        # Node filter
        st.header("🔍 Filters")
        all_nodes = db.get_all_nodes()
        node_options = ["All Nodes"] + [f"Node {n['id']}: {n['name']}" for n in all_nodes]
        selected_node = st.selectbox("Select Node", node_options)
        
        if selected_node == "All Nodes":
            filter_node_id = None
        else:
            filter_node_id = int(selected_node.split(":")[0].replace("Node ", ""))
        
        st.markdown("---")
        
        # Stats
        st.header("📊 Overall Statistics")
        total_tx = db.get_transaction_count()
        fraud_stats = db.get_fraud_stats()
        
        st.metric("Total Transactions", total_tx)
        st.metric("Total Fraud Checks", fraud_stats['total'])
        st.metric("Fraud Rate", f"{fraud_stats['fraud_rate']:.1f}%")
    
    # Main content
    
    # Fog Nodes Status Section
    st.header("🖥️ Fog Nodes Status")
    
    nodes = db.get_all_nodes()
    
    if not nodes:
        st.warning("No fog nodes configured. Please check your config.yaml file.")
    else:
        # Create columns for node cards
        cols = st.columns(min(3, len(nodes)))
        
        for idx, node in enumerate(nodes):
            # Get stats for this node
            tx_count = db.get_transaction_count(node['id'])
            fraud_stats_node = db.get_fraud_stats(node['id'])
            
            node_stats = {
                'total_tx': tx_count,
                'fraud_rate': fraud_stats_node['fraud_rate']
            }
            
            with cols[idx % 3]:
                render_node_card(node, node_stats)
    
    st.markdown("---")
    
    # Recent Transactions Section
    st.header("📋 Recent Transactions")
    
    max_display = config['dashboard']['max_transactions_display']
    transactions = db.get_recent_transactions(limit=max_display, node_id=filter_node_id)
    
    if not transactions:
        st.info("No transactions recorded yet. Waiting for data from fog nodes...")
    else:
        # Convert to DataFrame for better display
        tx_df = pd.DataFrame(transactions)
        
        # Format timestamp  
        if 'timestamp' in tx_df.columns:
            tx_df['time_ago'] = tx_df['timestamp'].apply(format_timestamp)
        
        # Prepare display columns with key transaction data (Class removed)
        display_cols = ['id', 'node_name', 'time', 'amount', 'time_ago']
        
        # Create clean display dataframe
        display_data = []
        for _, row in tx_df.head(20).iterrows():
            display_data.append({
                'ID': row['id'],
                'Node': row['node_name'],
                'Time': f"{row['time']:.0f}" if pd.notna(row.get('time')) else 'N/A',
                'Amount': f"${row['amount']:.2f}" if pd.notna(row.get('amount')) else 'N/A',
                'Recorded': row['time_ago']
            })
        
        display_df = pd.DataFrame(display_data)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Transaction volume chart
        if len(transactions) > 0:
            st.subheader("Transaction Volume Over Time")
            
            # Group by hour
            tx_df['timestamp_dt'] = pd.to_datetime(tx_df['timestamp'])
            tx_df['hour'] = tx_df['timestamp_dt'].dt.floor('H')
            
            volume_data = tx_df.groupby('hour').size().reset_index(name='count')
            
            fig = px.line(
                volume_data,
                x='hour',
                y='count',
                title='Transactions per Hour',
                labels={'hour': 'Time', 'count': 'Transaction Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Amount distribution
        if len(transactions) > 5 and 'amount' in tx_df.columns:
            st.subheader("Transaction Amount Distribution")
            
            fig = px.histogram(
                tx_df,
                x='amount',
                nbins=20,
                title='Distribution of Transaction Amounts',
                labels={'amount': 'Amount ($)', 'count': 'Frequency'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    
    st.markdown("---")
    
    # Recent Fraud Results Section
    st.header("🚨 Recent Fraud Detection Results")
    
    fraud_results = db.get_recent_fraud_results(limit=max_display, node_id=filter_node_id)
    
    if not fraud_results:
        st.info("No fraud detection results yet. Waiting for data from fog nodes...")
    else:
        # Convert to DataFrame
        fraud_df = pd.DataFrame(fraud_results)
        
        # Format timestamp
        if 'timestamp' in fraud_df.columns:
            fraud_df['time_ago'] = fraud_df['timestamp'].apply(format_timestamp)
        
        # Add status emoji based on prediction (0 = legitimate, 1 = fraud)
        fraud_df['status'] = fraud_df['prediction'].apply(lambda x: '🔴 FRAUD' if x == 1 else '🟢 LEGITIMATE')
        fraud_df['is_fraud'] = fraud_df['prediction'].apply(lambda x: x == 1)
        
        # Prepare display data
        display_data = []
        for _, row in fraud_df.head(20).iterrows():
            display_data.append({
                'ID': row['id'],
                'Node': row['node_name'],
                'Status': row['status'],
                'Time': f"{row['time']:.0f}" if pd.notna(row.get('time')) else 'N/A',
                'Recorded': row['time_ago']
            })
        
        display_df = pd.DataFrame(display_data)
        
        # Color code rows
        def highlight_fraud(row):
            if '🔴 FRAUD' in str(row['Status']):
                return ['background-color: rgba(255, 0, 0, 0.1)'] * len(row)
            else:
                return ['background-color: rgba(0, 255, 0, 0.05)'] * len(row)
        
        styled_df = display_df.style.apply(highlight_fraud, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Fraud rate by node
        if len(fraud_results) > 0:
            st.subheader("Fraud Rate by Node")
            
            fraud_by_node = fraud_df.groupby('node_name').agg({
                'is_fraud': ['count', 'sum']
            }).reset_index()
            
            fraud_by_node.columns = ['node_name', 'total', 'fraud_count']
            fraud_by_node['fraud_rate'] = (fraud_by_node['fraud_count'] / fraud_by_node['total'] * 100)
            
            fig = px.bar(
                fraud_by_node,
                x='node_name',
                y='fraud_rate',
                title='Fraud Rate by Fog Node (%)',
                labels={'node_name': 'Node', 'fraud_rate': 'Fraud Rate (%)'},
                color='fraud_rate',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Auto refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
