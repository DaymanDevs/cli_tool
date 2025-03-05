import json
import os
import pandas as pd
from utils import convert_fundtime_to_hours

DEFAULT_CRITERIA = {
    "Mcap": {"min": float('-inf'), "max": float('inf')},
    "Liq": {"min": float('-inf'), "max": float('inf')},
    "AG": {"min": float('-inf'), "max": float('inf')},
    "DevBal": {"max": float('inf')},
    "Funding": {"min": 0},
    "Bundle": {"max": float('inf')},
    "Links": None,
    "F": {"min": float('-inf'), "max": float('inf')},
    "KYC": {"min": float('-inf'), "max": float('inf')},
    "Unq": {"min": float('-inf'), "max": float('inf')},
    "SM": {"min": float('-inf'), "max": float('inf')},
    "MaxMcap": {"min": float('-inf'), "max": float('inf')},
    "X's": {"min": float('-inf')},
    "Targeted Feed": "PF",
}

def load_wallets():
    wallet_file = 'wallets.json'  # Root directory
    if os.path.exists(wallet_file):
        with open(wallet_file, 'r') as f:
            return json.load(f)
    return {}

def save_wallets(wallets):
    wallet_file = 'wallets.json'  # Root directory
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
        decision = "buy"
        for key, value in criteria.items():
            if key == "Links":
                if value is not None and row.get("Links") != value:
                    decision = f"{key} mismatch"
                    break
            elif key == "DevBal":
                max_val = value.get("max", float('inf'))
                col_value = row.get("DevBal", pd.NA)
                if pd.isna(col_value) or col_value > max_val:
                    decision = f"{key} too high"
                    break
            elif key == "Funding":
                min_val = value.get("min", 0)
                max_val = value.get("max", float('inf'))
                fund_time = row.get("Funding")
                if pd.isna(fund_time):
                    if min_val > 0 or max_val < float('inf'):
                        decision = f"{key} missing"
                        break
                else:
                    hours = convert_fundtime_to_hours(fund_time.split(' (')[0])
                    if hours < min_val:
                        decision = f"{key} too low"
                        break
                    elif hours > max_val:
                        decision = f"{key} too high"
                        break
            elif key == "Bundle":
                max_val = value.get("max", float('inf'))
                col_value = row.get("Bundle", pd.NA)
                if pd.isna(col_value) or col_value > max_val:
                    decision = f"{key} too high"
                    break
            elif key == "X's":
                min_val = value.get("min", float('-inf'))
                col_value = row.get("X's", pd.NA)
                if pd.isna(col_value) or col_value < min_val:
                    decision = f"{key} too low"
                    break
            elif key in ["Mcap", "Liq", "MaxMcap", "AG", "F", "KYC", "Unq", "SM"]:
                min_val = value.get("min", float('-inf'))
                max_val = value.get("max", float('inf'))
                col_value = row.get(key, pd.NA)
                if pd.isna(col_value):
                    decision = f"{key} missing"
                    break
                elif col_value < min_val:
                    decision = f"{key} too low"
                    break
                elif col_value > max_val:
                    decision = f"{key} too high"
                    break
        if decision == "buy" and pd.notna(row.get("X's")) and row["X's"] == 0:
            decision = "rug"
        decisions.append(decision)
    
    df[config_name] = decisions
    return df[config_name]