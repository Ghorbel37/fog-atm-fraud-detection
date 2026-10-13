"""
Train the fraud detection model without Jupyter.

Script version of the pipeline in notebooks/credit_card_fraud_detection_complete.ipynb
(Random Forest only, which is the model the notebook selects):
downloads the Kaggle dataset if needed, creates the two fog node simulation files,
trains a Random Forest on the remaining data and saves the model and scaler.

Usage (from the server/ folder):
    python src/train.py           # skips training if the model files already exist
    python src/train.py --force   # retrain anyway
"""

import argparse
import os
import urllib.request
import zipfile

import joblib
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

DATASET_URL = "https://www.kaggle.com/api/v1/datasets/download/mlg-ulb/creditcardfraud"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")
DATASET_PATH = os.path.join(DATA_DIR, "creditcard.csv")
MODEL_PATH = os.path.join(MODEL_DIR, "best_model_random_forest.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")


def download_dataset():
    """Download and extract creditcard.csv from Kaggle if it is not already there."""
    if os.path.exists(DATASET_PATH):
        return

    zip_path = os.path.join(DATA_DIR, "creditcardfraud.zip")
    print(f"Downloading dataset from {DATASET_URL} ...")
    urllib.request.urlretrieve(DATASET_URL, zip_path)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extract("creditcard.csv", DATA_DIR)
    os.remove(zip_path)
    print(f"Dataset saved to {DATASET_PATH}")


def take_simulation_sample(fraud_df, normal_df, random_state):
    """Sample 20 fraud + 2000 normal rows for one fog node, return them and the rest."""
    sim_fraud = fraud_df.sample(n=20, random_state=random_state)
    sim_normal = normal_df.sample(n=2000, random_state=random_state)
    simulation = pd.concat([sim_fraud, sim_normal]).sample(frac=1, random_state=random_state).reset_index(drop=True)
    return simulation, fraud_df.drop(sim_fraud.index), normal_df.drop(sim_normal.index)


def main():
    parser = argparse.ArgumentParser(description="Train the fog node fraud detection model.")
    parser.add_argument("--force", action="store_true", help="retrain even if the model files exist")
    args = parser.parse_args()

    if not args.force and os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        print(f"Model already trained ({MODEL_PATH}), skipping. Use --force to retrain.")
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)
    download_dataset()

    df = pd.read_csv(DATASET_PATH)
    fraud_df = df[df["Class"] == 1].copy()
    normal_df = df[df["Class"] == 0].copy()

    # Simulation data for the fog nodes (same split as the notebook)
    for node, random_state in ((1, 42), (2, 43)):
        simulation, fraud_df, normal_df = take_simulation_sample(fraud_df, normal_df, random_state)
        simulation.to_csv(os.path.join(DATA_DIR, f"simulation_node_{node}.csv"), index=False)
        print(f"Simulation node {node}: {len(simulation)} rows, {simulation['Class'].sum()} fraud")

    # Train/test split on the remaining data
    remaining_df = pd.concat([fraud_df, normal_df]).sample(frac=1, random_state=42).reset_index(drop=True)
    train_df, test_df = train_test_split(
        remaining_df, test_size=0.2, stratify=remaining_df["Class"], random_state=42
    )
    X_train, y_train = train_df.drop("Class", axis=1), train_df["Class"]
    X_test, y_test = test_df.drop("Class", axis=1), test_df["Class"]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("Applying SMOTE...")
    X_train_balanced, y_train_balanced = SMOTE(random_state=42).fit_resample(X_train_scaled, y_train)

    print("Training Random Forest (this can take a few minutes)...")
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train_balanced, y_train_balanced)

    y_pred = model.predict(X_test_scaled)
    print(f"Test recall:    {recall_score(y_test, y_pred):.4f}")
    print(f"Test precision: {precision_score(y_test, y_pred):.4f}")
    print(f"Test F1-score:  {f1_score(y_test, y_pred):.4f}")

    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"Model saved to {MODEL_PATH}")
    print(f"Scaler saved to {SCALER_PATH}")


if __name__ == "__main__":
    main()
