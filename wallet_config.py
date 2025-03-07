import json
import os
from config import WALLETS_FILE

DEFAULT_CRITERIA = {
    "Mcap": {"min": float('-inf'), "max": float('inf')},
    "Liq": {"min": float('-inf'), "max": float('inf')},
    "AG": {"min": float('-inf'), "max": float('inf')},
    "Bundle": {"max": float('inf')},
    "Funding": {"min": 0},
    "Dev%": {"max": float('inf')},
    "DevBal": {"max": float('inf')},
    "Links": None,
    "F": {"min": float('-inf'), "max": float('inf')},
    "KYC": {"min": float('-inf'), "max": float('inf')},
    "Unq": {"min": float('-inf'), "max": float('inf')},
    "SM": {"min": float('-inf'), "max": float('inf')},
    "X's": {"min": float('-inf')}
}

def load_wallets():
    if not os.path.exists(WALLETS_FILE):
        return {}
    with open(WALLETS_FILE, 'r') as f:
        return json.load(f)

def save_wallets(wallets):
    os.makedirs(os.path.dirname(WALLETS_FILE), exist_ok=True)
    with open(WALLETS_FILE, 'w') as f:
        json.dump(wallets, f, indent=4)

def apply_wallet_config(df, config_name, criteria):
    df = df.copy()
    result = []
    for _, row in df.iterrows():
        meets_criteria = True
        for key, condition in criteria.items():
            if key not in df.columns:
                continue
            value = row[key]
            if pd.isna(value):
                meets_criteria = False
                break
            if key == "Links":
                if condition is not None and value != condition:
                    meets_criteria = False
            elif key in ["Mcap", "Liq", "AG", "F", "KYC", "Unq", "SM", "DevBal"]:
                min_val = condition.get("min", float('-inf'))
                max_val = condition.get("max", float('inf'))
                if not (min_val <= value <= max_val):
                    meets_criteria = False
            elif key in ["Bundle", "Dev%"]:
                max_val = condition.get("max", float('inf'))
                if value > max_val:
                    meets_criteria = False
            elif key == "Funding":
                min_val = condition.get("min", 0)
                from utils import convert_fundtime_to_hours
                hours = convert_fundtime_to_hours(value.split(' (')[0]) if '(' in value else float('nan')
                if pd.isna(hours) or hours < min_val:
                    meets_criteria = False
            elif key == "X's":
                min_val = condition.get("min", float('-inf'))
                if value < min_val:
                    meets_criteria = False
        result.append("buy" if meets_criteria else "skip")
    return result

def create_wallet_config(name, criteria):
    wallets = load_wallets()
    wallets[name] = criteria
    save_wallets(wallets)

def duplicate_wallet_config(original_name, new_name):
    wallets = load_wallets()
    if original_name in wallets:
        wallets[new_name] = wallets[original_name].copy()
        save_wallets(wallets)