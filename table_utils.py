import pandas as pd
from ui_utils import menu_selection, format_filter_display
from wallet_config import load_wallets
import os
import json
from config import WALLETS_FILE

def filter_table(df, table_name, existing_filters):
    filter_options = [col for col in df.columns if col not in ['#', 'Iteration']] + ["Back"]
    filters = existing_filters.copy()
    table_str = "\n".join([format_filter_display(k, v) for k, v in filters.items()]) if filters else "No filters applied."
    is_top_table = 'token_name' in df.columns
    
    while True:
        choice = menu_selection(filter_options, table_str, prompt=f"Filter {table_name} by:")
        if choice == "Back" or choice is None:
            break
        
        column = choice
        if column in ["Name", "Links", "FreshDeployer", "Desc", "token_name"]:
            value = menu_selection(filter_options, table_str, prompt=f"Enter {column} value (or blank for any): ", allow_input=True)
            if value:
                filters[column] = value
            elif column in filters:
                del filters[column]
        elif column == "Date" and not is_top_table:
            min_date = menu_selection(filter_options, table_str, prompt="Enter min date (DD/MM/YY HH:MM or blank): ", allow_input=True)
            max_date = menu_selection(filter_options, table_str, prompt="Enter max date (DD/MM/YY HH:MM or blank): ", allow_input=True)
            min_val = pd.to_datetime(min_date, format='%d/%m/%y %H:%M', errors='coerce') if min_date else float('-inf')
            max_val = pd.to_datetime(max_date, format='%d/%m/%y %H:%M', errors='coerce') if max_date else float('inf')
            if pd.isna(min_val) and min_date:
                print("Invalid min date format. Press any key to continue...")
                input()
                continue
            if pd.isna(max_val) and max_date:
                print("Invalid max date format. Press any key to continue...")
                input()
                continue
            filters[column] = (min_val, max_val)
        elif column in ["Liq%", "Bundle", "Dev%", "B-Ratio"] and not is_top_table:
            max_val = menu_selection(filter_options, table_str, prompt=f"Enter max {column} % (or blank): ", allow_input=True)
            try:
                max_float = float(max_val) / 100 if max_val else float('inf')
                filters[column] = {"max": max_float}
            except ValueError:
                print("Invalid number format. Press any key to continue...")
                input()
        elif column == "FundingTime" and not is_top_table:
            min_val = menu_selection(filter_options, table_str, prompt="Enter min FundingTime (e.g., '14h', or blank): ", allow_input=True)
            try:
                min_float = float(min_val.replace('h', '')) if min_val else 0
                filters[column] = {"min": min_float}
            except ValueError:
                print("Invalid number format. Press any key to continue...")
                input()
        else:
            min_val = menu_selection(filter_options, table_str, prompt=f"Enter min {column} (or blank): ", allow_input=True)
            max_val = menu_selection(filter_options, table_str, prompt=f"Enter max {column} (or blank): ", allow_input=True)
            try:
                min_float = float(min_val) if min_val else float('-inf')
                max_float = float(max_val) if max_val else float('inf')
                filters[column] = (min_float, max_float)
            except ValueError:
                print("Invalid number format. Press any key to continue...")
                input()
        
        table_str = "\n".join([format_filter_display(k, v) for k, v in filters.items()]) if filters else "No filters applied."
    
    filtered_df = df.copy()
    for column, value in filters.items():
        if column in ["Name", "Links", "FreshDeployer", "Desc", "token_name"]:
            filtered_df = filtered_df[filtered_df[column] == value]
        elif column == "Date":
            min_val, max_val = value
            filtered_df = filtered_df[(filtered_df[column] >= min_val) & (filtered_df[column] <= max_val)]
        elif column in ["Liq%", "Bundle", "Dev%", "B-Ratio"]:
            filtered_df = filtered_df[filtered_df[column] <= value["max"]]
        elif column == "FundingTime":
            filtered_df = filtered_df[filtered_df[column].str.extract(r'(\d+)')[0].astype(float) >= value["min"]]
        else:
            min_val, max_val = value
            filtered_df = filtered_df[(filtered_df[column] >= min_val) & (filtered_df[column] <= max_val)]
    
    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df['#'] = range(1, len(filtered_df) + 1)
    return filtered_df, filters

def generate_wallet_summary(df, config_names):
    if not config_names:
        return ""
    summary = []
    for name in config_names:
        if name in df.columns:
            buy_count = (df[name] == "buy").sum()
            skip_count = (df[name] == "skip").sum()
            summary.append(f"{name}: {buy_count} buy, {skip_count} skip")
    return "\n".join(summary) if summary else ""

def search_contracts_in_pf(contracts, conn, df):
    pf_df = pd.read_sql_query(f"SELECT token, Date, Mcap, Liq FROM pf WHERE token IN ({','.join(['?']*len(contracts))})", conn, params=contracts)
    if not pf_df.empty:
        merged_df = df.merge(pf_df, on='token', how='left', suffixes=('', '_pf'))
        merged_df['MaxMcap'] = merged_df[['MaxMcap', 'Mcap_pf']].max(axis=1)
        merged_df['X\'s'] = (merged_df['MaxMcap'] / merged_df['Mcap']).replace([float('inf'), -float('inf')], 0).fillna(0)
        return merged_df.drop(columns=['Mcap_pf', 'Liq_pf', 'Date_pf'], errors='ignore')
    return df

def generate_wallet_config_from_rows(df):
    config = {}
    is_top_table = 'token_name' in df.columns
    if is_top_table:
        for col in ['start_mcap', 'end_mcap', "X's"]:
            if col in df.columns:
                min_val = df[col].min()
                max_val = df[col].max()
                config[col] = {"min": min_val if pd.notna(min_val) else float('-inf'), 
                              "max": max_val if pd.notna(max_val) else float('inf')}
    else:
        for col in ['Mcap', 'Liq', 'AG', 'DevBal', 'F', 'KYC', 'Unq', 'SM', "X's", 'TTC', 'Drained']:
            if col in df.columns:
                min_val = df[col].min()
                max_val = df[col].max()
                config[col] = {"min": min_val if pd.notna(min_val) else float('-inf'), 
                              "max": max_val if pd.notna(max_val) else float('inf')}
        for col in ['Liq%', 'Bundle', 'Dev%', 'B-Ratio']:
            if col in df.columns:
                min_val = df[col].min()
                max_val = df[col].max()
                config[col] = {"min": min_val if pd.notna(min_val) else float('-inf'), 
                              "max": max_val if pd.notna(max_val) else float('inf')}
        if 'FundingTime' in df.columns:
            funding_mins = df['FundingTime'].str.extract(r'(\d+)').astype(float).dropna()
            config['FundingTime'] = {"min": funding_mins.min() if not funding_mins.empty else 0}
        if 'Links' in df.columns:
            config['Links'] = "Yes" if df['Links'].all() else "Any"
        if 'FreshDeployer' in df.columns:
            config['FreshDeployer'] = "Yes" if df['FreshDeployer'].all() else "Any"
        if 'Desc' in df.columns:
            config['Desc'] = "Yes" if df['Desc'].all() else "Any"
    return config