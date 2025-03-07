import pandas as pd
import sqlite3
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

def get_db_connection():
    return sqlite3.connect(os.path.join(DATA_DIRECTORY, 'data.db'))

def load_mcaps_db(conn):
    # Updated to use 'token' instead of 'Contract'
    df = pd.read_sql_query("SELECT token, MaxMcap FROM mcaps", conn)
    logging.debug(f"MCAPS loaded from DB - {len(df)} rows, First 5 tokens: {df['token'].tolist()[:5]}")
    return df

def load_and_combine_csv(directory):
    if not os.path.exists(os.path.join(directory, 'data.db')):
        print(f"Error: Database not found at {directory}/data.db. Run init_db.py first.")
        return None
    conn = get_db_connection()
    return conn  # Return connection instead of combined tables