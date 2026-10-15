# MQTT communication

## Topics

- **`fog/transactions/raw`** - Raw transaction data from fog nodes
- **`fog/transactions/results`** - Fraud prediction results from fog nodes

## Message Formats

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
