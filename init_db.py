import pandas as pd
import sqlite3
import os
import json
from config import DATA_DIRECTORY

def init_database(force_rebuild=False):
    db_path = os.path.join(DATA_DIRECTORY, 'data.db')
    processed_file = os.path.join(DATA_DIRECTORY, 'processed_files.json')
    
    # Load or reset processed files tracking
    processed_files = {}
    if os.path.exists(processed_file) and not force_rebuild:
        with open(processed_file, 'r') as f:
            processed_files = json.load(f)
    if force_rebuild and os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all CSV files
    all_files = [f for f in os.listdir(DATA_DIRECTORY) if f.lower().endswith('.csv')]
    print(f"Found {len(all_files)} CSV files in {DATA_DIRECTORY}: {', '.join(all_files[:5])}...")
    
    # Classify files (ensure mutual exclusivity)
    top_csv_files = [f for f in all_files if '10' in f.split('-')[0].lower() and not f.lower().startswith('mcaps-')]
    mcaps_files = [f for f in all_files if f.lower().startswith('mcaps-')]
    regular_csv_files = [f for f in all_files if f not in top_csv_files and f not in mcaps_files]
    
    print(f"Detected {len(top_csv_files)} Top CSVs: {', '.join(top_csv_files[:5])}..." if top_csv_files else "No Top CSVs detected.")
    
    # Filter new/modified files
    def get_new_files(file_list):
        new_files = []
        for f in file_list:
            full_path = os.path.join(DATA_DIRECTORY, f)
            mtime = os.path.getmtime(full_path)
            if full_path not in processed_files or processed_files[full_path] < mtime or force_rebuild:
                new_files.append(full_path)
                processed_files[full_path] = mtime
        return new_files
    
    new_regular_csvs = get_new_files(regular_csv_files)
    new_top_csvs = get_new_files(top_csv_files)
    new_mcaps = get_new_files(mcaps_files)
    
    if not any([new_regular_csvs, new_top_csvs, new_mcaps]):
        print("No new or modified CSVs to process.")
    else:
        print(f"Processing {len(new_regular_csvs)} regular CSVs, {len(new_top_csvs)} Top CSVs, {len(new_mcaps)} MCAPS files...")
        
        # Regular CSVs (append)
        for file in new_regular_csvs:
            base_name = os.path.basename(file).replace('.csv', '')
            feed_name = base_name.split('-')[0].lower().replace(' ', '_')
            df = pd.read_csv(file)
            
            if 'Contract' in df.columns:
                df = df.rename(columns={'Contract': 'token'})
            elif 'contract' in df.columns:
                df = df.rename(columns={'contract': 'token'})
            if 'token' not in df.columns:
                print(f"Warning: No 'token' or 'contract' column in {file}. Skipping.")
                continue
            if 'token_name' in df.columns:
                df = df.rename(columns={'token_name': 'Name'})
            df['token'] = df['token'].apply(lambda x: f"{str(x)[:8]}..." if len(str(x)) > 8 else str(x))
            
            numeric_cols = ["Mcap", "Liq", "AG", "DevBal", "F", "KYC", "Unq", "SM", "TTC", "Drained"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].replace('[\\$,]', '', regex=True), errors='coerce')
            
            percent_cols = ["Liq%", "Bundle", "Dev%", "B-Ratio"]
            for col in percent_cols:
                if col in df.columns:
                    df[col] = df[col].replace({'%': ''}, regex=True).astype(float) / 100
            
            if 'Timestamp' in df.columns:
                df['Date'] = pd.to_datetime(df['Timestamp'], errors='coerce')
                df = df.drop(columns=['Timestamp'], errors='ignore')
            
            string_cols = ["Name", "FundingTime", "FundingSource", "Links", "FreshDeployer", "Desc"]
            for col in string_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).fillna('')
            
            if 'FundingTime' in df.columns and 'FundingSource' in df.columns:
                df['Funding'] = df['FundingTime'] + ' (' + df['FundingSource'] + ')'
            
            expected_cols = ['token', 'Date', 'Name', 'Mcap', 'Liq', 'Liq%', 'AG', 'Bundle', 
                             'FundingTime', 'FundingSource', 'Funding', 'Dev%', 'DevBal', 'Links', 
                             'F', 'KYC', 'Unq', 'SM', 'TTC', 'B-Ratio', 'FreshDeployer', 'Drained', 'Desc']
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = 0.0 if col in numeric_cols or col in percent_cols else ''
            df = df[expected_cols]
            
            if force_rebuild and file == new_regular_csvs[0]:
                cursor.execute(f"DROP TABLE IF EXISTS {feed_name}")
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {feed_name} (
                    token TEXT,
                    Date DATETIME,
                    Name TEXT,
                    Mcap REAL,
                    Liq REAL,
                    "Liq%" REAL,
                    AG REAL,
                    Bundle REAL,
                    FundingTime TEXT,
                    FundingSource TEXT,
                    Funding TEXT,
                    "Dev%" REAL,
                    DevBal REAL,
                    Links TEXT,
                    F REAL,
                    KYC REAL,
                    Unq REAL,
                    SM REAL,
                    TTC REAL,
                    "B-Ratio" REAL,
                    FreshDeployer TEXT,
                    Drained REAL,
                    Desc TEXT
                )
            """)
            df.to_sql(feed_name, conn, if_exists='append', index=False, chunksize=40, method='multi')
            cursor.execute(f"SELECT COUNT(*) FROM {feed_name}")
            total_rows = cursor.fetchone()[0]
            print(f"Added {feed_name} with {len(df)} new rows (total now {total_rows})")
        
        # Top CSVs (upsert)
        for file in new_top_csvs:
            base_name = os.path.basename(file).replace('.csv', '')
            feed_name = base_name.split('-')[0].lower().replace(' ', '_')
            df = pd.read_csv(file)
            
            if 'Contract' not in df.columns and 'contract' in df.columns:
                df = df.rename(columns={'contract': 'Contract'})
            if 'Contract' not in df.columns:
                print(f"Warning: No 'Contract' or 'contract' column in {file}. Skipping.")
                continue
            if 'token_name' in df.columns:
                df = df.rename(columns={'token_name': 'Name'})
            if 'start_mcap' in df.columns and 'end_mcap' in df.columns:
                df = df.rename(columns={'start_mcap': 'Mcap', 'end_mcap': 'HighestMcap', 'profit_multiples': 'Multiples'})
            df['Contract'] = df['Contract'].apply(lambda x: f"{str(x)[:8]}..." if len(str(x)) > 8 else str(x))
            
            numeric_cols = ['Mcap', 'HighestMcap']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            if 'Multiples' in df.columns:
                df['Multiples'] = pd.to_numeric(df['Multiples'].str.replace('x', ''), errors='coerce')
            if 'Name' in df.columns:
                df['Name'] = df['Name'].astype(str).fillna('')
            
            expected_cols = ['Contract', 'Name', 'Mcap', 'HighestMcap', 'Multiples']
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = 0.0 if col in numeric_cols or col == 'Multiples' else ''
            df = df[expected_cols]
            
            if force_rebuild and file == new_top_csvs[0]:
                cursor.execute(f"DROP TABLE IF EXISTS {feed_name}")
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {feed_name} (
                    Contract TEXT PRIMARY KEY,
                    Name TEXT,
                    Mcap REAL,
                    HighestMcap REAL,
                    Multiples REAL
                )
            """)
            for _, row in df.iterrows():
                cursor.execute(f"""
                    INSERT OR REPLACE INTO {feed_name} (Contract, Name, Mcap, HighestMcap, Multiples)
                    VALUES (?, ?, ?, ?, ?)
                """, (row['Contract'], row['Name'], row['Mcap'], row['HighestMcap'], row['Multiples']))
            cursor.execute(f"SELECT COUNT(*) FROM {feed_name}")
            total_rows = cursor.fetchone()[0]
            print(f"Updated {feed_name} with {len(df)} rows processed (total now {total_rows})")
        
        # MCAPS (upsert)
        if new_mcaps:
            mcaps_df = pd.concat([pd.read_csv(f) for f in new_mcaps], ignore_index=True)
            if 'token' not in mcaps_df.columns and 'contract' in mcaps_df.columns:
                mcaps_df = mcaps_df.rename(columns={'contract': 'token'})
            if 'token' not in mcaps_df.columns:
                print(f"Warning: No 'token' or 'contract' column in MCAPS files. Skipping.")
            else:
                mcaps_df['token'] = mcaps_df['token'].apply(lambda x: f"{str(x)[:8]}..." if len(str(x)) > 8 else str(x))
                if 'market_cap_usd' in mcaps_df.columns:
                    mcaps_df['Mcap'] = pd.to_numeric(mcaps_df['market_cap_usd'].replace('[\\$,]', '', regex=True), errors='coerce')
                if 'max_market_cap_usd' in mcaps_df.columns:
                    mcaps_df['MaxMcap'] = pd.to_numeric(mcaps_df['max_market_cap_usd'].replace('[\\$,]', '', regex=True), errors='coerce')
                mcaps_df = mcaps_df[['token', 'Mcap', 'MaxMcap']].dropna(subset=['token'])
                
                if force_rebuild:
                    cursor.execute("DROP TABLE IF EXISTS mcaps")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS mcaps (
                        token TEXT PRIMARY KEY,
                        Mcap REAL,
                        MaxMcap REAL
                    )
                """)
                for _, row in mcaps_df.iterrows():
                    cursor.execute("""
                        INSERT OR REPLACE INTO mcaps (token, Mcap, MaxMcap)
                        VALUES (?, ?, ?)
                    """, (row['token'], row['Mcap'], row['MaxMcap']))
                cursor.execute("SELECT COUNT(*) FROM mcaps")
                total_rows = cursor.fetchone()[0]
                print(f"Updated mcaps with {len(mcaps_df)} rows processed (total now {total_rows})")
    
    # Save processed files
    with open(processed_file, 'w') as f:
        json.dump(processed_files, f)
    
    # Add indexes
    for table in pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)['name']:
        if table != 'mcaps':
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            if 'token' in columns:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_token ON {table} (token)")
            elif 'Contract' in columns:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_contract ON {table} (Contract)")
            if 'Date' in columns:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_date ON {table} (Date)")
    
    conn.commit()
    conn.close()
    print("Database updated with new CSVs and indexes.")

if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    init_database(force_rebuild=force)