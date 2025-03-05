import pandas as pd
import os
import platform
import logging
from config import DATA_DIRECTORY

logging.basicConfig(
    filename='debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s',
    filemode='w'
)

def load_mcaps_csv(directory):
    mcaps_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.startswith('MCAPS-') and f.endswith('.csv')]
    if not mcaps_files:
        logging.debug("No MCAPS files found in 'data/' directory.")
        return pd.DataFrame()
    
    mcaps_dfs = []
    for file in mcaps_files:
        df = pd.read_csv(file)
        mcaps_dfs.append(df)
    
    combined_mcaps = pd.concat(mcaps_dfs, ignore_index=True)
    combined_mcaps = combined_mcaps.sort_values('max_market_cap_usd', ascending=False).drop_duplicates('token', keep='first')
    combined_mcaps = combined_mcaps.rename(columns={'token': 'Contract', 'max_market_cap_usd': 'MaxMcap'})
    logging.debug(f"MCAPS loaded - {len(combined_mcaps)} rows, First 5 Contracts: {combined_mcaps['Contract'].tolist()[:5]}")
    return combined_mcaps[['Contract', 'MaxMcap']]

def load_and_combine_csv(directory):
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' not found.")
        return {}
    
    csv_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv') and not f.startswith('MCAPS-')]
    tables = {}
    
    logging.debug(f"Loading CSV files from '{directory}' - {len(csv_files)} files found")
    for file in csv_files:
        df = pd.read_csv(file)
        numeric_cols = ["Mcap", "Liq", "AG", "Dev Bal", "F", "KYC", "Unq", "SM"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        percent_cols = ["Bundle", "Dev%"]
        for col in percent_cols:
            if col in df.columns:
                df[col] = df[col].replace({'%': ''}, regex=True).astype(float) / 100
        if 'Multiples' in df.columns:
            df['X\'s'] = df['Multiples'].replace({'x': ''}, regex=True).astype(float)
            df = df.drop(columns=['Multiples'], errors='ignore')
        if 'HighestMcap' in df.columns:
            df = df.rename(columns={'HighestMcap': 'MaxMcap'})
        if 'Funding Time' in df.columns and 'Funding Source' in df.columns:
            df['Funding'] = df.apply(lambda row: f"{row['Funding Time']} ({row['Funding Source']})" if pd.notna(row['Funding Time']) and pd.notna(row['Funding Source']) else pd.NA, axis=1)
            df = df.drop(columns=['Funding Time', 'Funding Source'], errors='ignore')
        name = os.path.basename(file).split('-')[0].lower()
        tables.setdefault(name, []).append(df)
        logging.debug(f"Loaded '{file}' into table '{name}' - {len(df)} rows")
    
    mcaps_df = load_mcaps_csv(directory)
    
    # Collect ALL Top table data first
    top_tables = {key: df for key, df in tables.items() if key.endswith("10")}
    top_maxmcap = pd.DataFrame()
    for top_df_list in top_tables.values():
        for top_df in top_df_list:
            if 'MaxMcap' in top_df.columns and 'Contract' in top_df.columns:
                top_subset = top_df[['Contract', 'MaxMcap', 'X\'s']].dropna(subset=['MaxMcap'])
                top_maxmcap = pd.concat([top_maxmcap, top_subset], ignore_index=True)
    if not top_maxmcap.empty:
        top_maxmcap = top_maxmcap.drop_duplicates('Contract', keep='first')
        logging.debug(f"TOP data loaded - {len(top_maxmcap)} rows, First 5 Contracts: {top_maxmcap['Contract'].tolist()[:5]}")
    else:
        logging.debug("No valid TOP data found after processing.")
    
    combined_tables = {}
    for name, dfs in tables.items():
        combined_df = pd.concat(dfs, ignore_index=True)
        logging.debug(f"Processing table '{name}' - {len(combined_df)} rows initially")
        
        if name.endswith("10"):
            if 'X\'s' in combined_df.columns:
                combined_df['X\'s'] = combined_df['X\'s'].replace({'x': ''}, regex=True).astype(float)
                combined_df = combined_df.drop_duplicates('Contract', keep='first')
            # Top tables keep their MaxMcap and X's
            logging.debug(f"Top table '{name}' processed - MaxMcap NaN count: {combined_df['MaxMcap'].isna().sum()}")
        else:
            if name in ['pf', 'sm', 'gm']:
                combined_df = combined_df.sort_values(["Date", "Time"], ascending=[False, False])
                combined_df.insert(0, "Iteration", combined_df.groupby("Contract").cumcount() + 1)
                combined_df = combined_df.reset_index(drop=True)
            
            # Apply Top data first (highest priority)
            if not top_maxmcap.empty:
                combined_df = combined_df.merge(top_maxmcap[['Contract', 'MaxMcap', 'X\'s']], on='Contract', how='left', suffixes=('', '_top'))
                # Check if '_top' columns exist before accessing
                if 'MaxMcap_top' in combined_df.columns:
                    combined_df['MaxMcap'] = combined_df['MaxMcap_top'].fillna(combined_df['MaxMcap'])
                    combined_df['X\'s'] = combined_df['X\'s_top'].fillna(combined_df['X\'s'])
                    combined_df = combined_df.drop(columns=['MaxMcap_top', 'X\'s_top'], errors='ignore')
                else:
                    logging.debug(f"No 'MaxMcap_top' after merge for '{name}' - likely no matching contracts")
                logging.debug(f"After TOP merge for '{name}' - MaxMcap NaN count: {combined_df['MaxMcap'].isna().sum()}")
            else:
                combined_df['MaxMcap'] = combined_df.get('MaxMcap', pd.NA)
                combined_df['X\'s'] = combined_df.get('X\'s', pd.NA)
            
            # Apply MCAPS only if no Top data
            if not mcaps_df.empty:
                combined_df = combined_df.merge(mcaps_df, on='Contract', how='left', suffixes=('', '_mcaps'))
                if 'MaxMcap_mcaps' in combined_df.columns:
                    combined_df['MaxMcap'] = combined_df['MaxMcap'].fillna(combined_df['MaxMcap_mcaps'])
                    combined_df['X\'s'] = combined_df['X\'s'].fillna(combined_df['MaxMcap'] / combined_df['Mcap']).replace([float('inf'), -float('inf')], 0)
                    combined_df = combined_df.drop(columns=['MaxMcap_mcaps'], errors='ignore')
                logging.debug(f"After MCAPS merge for '{name}' - MaxMcap NaN count: {combined_df['MaxMcap'].isna().sum()}")
            
            combined_df['MaxMcap'] = combined_df['MaxMcap'].fillna(0)
            combined_df['X\'s'] = combined_df['X\'s'].fillna(0).replace([float('inf'), -float('inf')], 0)
        
        combined_tables[name] = combined_df
    
    return combined_tables