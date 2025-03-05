import json
import os
import pandas as pd  # Added import
from config import DATA_DIRECTORY
from utils import convert_fundtime_to_hours

DEFAULT_CRITERIA = {
    "Mcap": {"min": float('-inf'), "max": float('inf')},
    "Liq": {"min": float('-inf'), "max": float('inf')},
    "AG": {"min": float('-inf'), "max": float('inf')},
    "DevBal": {"max": float('inf')},
    "Funding": {"min": 0},  # Updated to match wallets.json structure
    "Bundle": {"max": float('inf')},
    "Links": None,
    "F": {"min": float('-inf'), "max": float('inf')},
    "KYC": {"min": float('-inf'), "max": float('inf')},
    "Unq": {"min": float('-inf'), "max": float('inf')},
    "SM": {"min": float('-inf'), "max": float('inf')},
    "MaxMcap": {"min": float('-inf'), "max": float('inf')},
    "X's": {"min": float('-inf'), "max": float('inf')},
    "Targeted Feed": "PF",
}

def load_wallets():
    wallet_file = os.path.join(DATA_DIRECTORY, 'wallets.json')
    if os.path.exists(wallet_file):
        with open(wallet_file, 'r') as f:
            return json.load(f)
    return {}

def save_wallets(wallets):
    wallet_file = os.path.join(DATA_DIRECTORY, 'wallets.json')
    with open(wallet_file, 'w') as f:
        json.dump(wallets, f, indent=4)

def create_wallet_config(name, criteria):
    wallets = load_wallets()
    wallets[name] = criteria
    save_wallets(wallets)

def duplicate_wallet_config(original_name, new_name):
    wallets = load_wallets()
    if original_name in wallets:
        wallets[new_name] = wallets[original_name].copy()
        save_wallets(wallets)

def apply_wallet_config(df, config_name, criteria):
    df = df.copy()
    decisions = []
    
    for _, row in df.iterrows():
        decision = "skip"
        for key, value in criteria.items():
            if key == "Links":
                if value is not None and row.get("Links") != value:
                    decision = "skip"
                    break
            elif key == "DevBal":
                max_val = value["max"]
                if max_val != float('inf') and (pd.isna(row.get("DevBal")) or row["DevBal"] > max_val):
                    decision = "skip"
                    break
            elif key == "Funding":
                min_val = value["min"]
                if min_val != 0 and (pd.isna(row.get("Funding")) or convert_fundtime_to_hours(row["Funding"].split(' (')[0]) < min_val):
                    decision = "skip"
                    break
            elif key == "Bundle":
                max_val = value["max"]
                if max_val != float('inf') and (pd.isna(row.get("Bundle")) or row["Bundle"] > max_val):
                    decision = "skip"
                    break
            elif key in ["Mcap", "Liq", "MaxMcap", "X's"]:
                min_val = value["min"]
                max_val = value["max"]
                col_value = row.get(key, pd.NA)
                if pd.isna(col_value) or col_value < min_val or col_value > max_val:
                    decision = "skip"
                    break
            elif key in ["AG", "F", "KYC", "Unq", "SM"]:
                min_val = value["min"]
                max_val = value["max"]
                col_value = row.get(key, pd.NA)
                if pd.isna(col_value) or col_value < min_val or col_value > max_val:
                    decision = "skip"
                    break
        else:
            decision = "buy"
            if pd.notna(row.get("X's")) and row["X's"] == 0:
                decision = "rug"
        decisions.append(decision)
    
    df[config_name] = decisions
    return df[config_name]