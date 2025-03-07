import pandas as pd
import sqlite3
import os
import json
from config import DATA_DIRECTORY

def init_database():
    db_path = os.path.join(DATA_DIRECTORY, 'data.db')
    processed_file = os.path.join(DATA_DIRECTORY, 'processed_files.json')
    
    # Load previously processed files
    processed_files = {}
    if os.path.exists(processed_file):
        with open(processed_file, 'r') as f:
            processed_files = json.load(f)
    
    conn = sqlite3.connect(db_path)
    csv_files = [os.path.abspath(os.path.join(DATA_DIRECTORY, f)) for f in os.listdir(DATA_DIRECTORY) if f.endswith('.csv') and not f.startswith('MCAPS-')]
    mcaps_files = [os.path.abspath(os.path.join(DATA_DIRECTORY, f)) for f in os.listdir(DATA_DIRECTORY) if f.startswith('MCAPS-') and f.endswith('.csv')]
    
    new_csvs = []
    for file in csv_files:
        mtime = os.path.getmtime(file)
        if file not in processed_files or processed_files[file] < mtime:
            new_csvs.append(file)
            processed_files[file] = mtime
    
    new_mcaps = []
    for file in mcaps_files:
        mtime = os.path.getmtime(file)
        if file not in processed_files or processed_files[file] < mtime:
            new_mcaps.append(file)
            processed_files[file] = mtime
    
    if not new_csvs and not new_mcaps:
        print("No new or modified CSVs to process.")
    else:
        print(f"Processing {len(new_csvs)} new/modified CSVs and {len(new_mcaps)} new/modified MCAPS files...")
        for file in new_csvs:
            feed_name = os.path.basename(file).split('-')[0].lower()
            df = pd.read_csv(file)
            # Rename 'Contract' to 'token'
            if 'Contract' in df.columns:
                df = df.rename(columns={'Contract': 'token'})
            numeric_cols = ["Mcap", "Liq", "AG", "Dev Bal", "F", "KYC", "Unq", "SM"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            percent_cols = ["Bundle", "Dev%"]
            for col in percent_cols:
                if col in df.columns:
                    df[col] = df[col].replace({'%': ''}, regex=True).astype(float) / 100
            if 'HighestMcap' in df.columns:
                df['MaxMcap'] = pd.to_numeric(df['HighestMcap'], errors='coerce')
                df = df.drop(columns=['HighestMcap'], errors='ignore')
            if 'Funding Time' in df.columns and 'Funding Source' in df.columns:
                df['Funding'] = df.apply(lambda row: f"{row['Funding Time']} ({row['Funding Source']})" if pd.notna(row['Funding Time']) and pd.notna(row['Funding Source']) else pd.NA, axis=1)
                df = df.drop(columns=['Funding Time', 'Funding Source'], errors='ignore')
            if 'Date' in df.columns and 'Time' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], dayfirst=True, errors='coerce', format='%d/%m/%y %H:%M')
                df = df.drop(columns=['Time'], errors='ignore')
            df.to_sql(feed_name, conn, if_exists='append', index=False)
            print(f"Added {feed_name} with {len(df)} rows")
        
        if new_mcaps:
            mcaps_df = pd.concat([pd.read_csv(f) for f in new_mcaps], ignore_index=True)
            # Rename 'token' to match database schema
            mcaps_df = mcaps_df.rename(columns={'token': 'token', 'max_market_cap_usd': 'MaxMcap'})
            # Keep only relevant columns
            mcaps_df = mcaps_df[['token', 'MaxMcap']]
            existing_mcaps = pd.read_sql_query("SELECT token, MaxMcap FROM mcaps", conn) if 'mcaps' in pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)['name'].values else pd.DataFrame(columns=['token', 'MaxMcap'])
            if not existing_mcaps.empty:
                mcaps_df = pd.concat([existing_mcaps, mcaps_df], ignore_index=True)
            mcaps_df = mcaps_df.sort_values('MaxMcap', ascending=False).drop_duplicates('token', keep='first')
            conn.execute("DROP TABLE IF EXISTS mcaps")
            mcaps_df.to_sql('mcaps', conn, if_exists='replace', index=False)
            print(f"Updated mcaps with {len(mcaps_df)} rows")
    
    # Update processed files list
    with open(processed_file, 'w') as f:
        json.dump(processed_files, f)
    
    # Create indexes with 'token'
    cursor = conn.cursor()
    existing_tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)['name'].tolist()
    for table in ['pf', 'fomo', 'bb', 'gm', 'mf', 'sm', 'pf10', 'fomo10', 'bb10', 'gm10', 'mf10', 'sm10']:
        if table in existing_tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            if 'token' in columns:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_token ON {table} (token)")
            if 'Date' in columns:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_date ON {table} (Date)")
    conn.commit()
    conn.close()
    print("Database updated with new CSVs and indexes.")

if __name__ == "__main__":
    init_database()