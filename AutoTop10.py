import os
import json
import csv
import argparse
from datetime import datetime
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

# Function to open a file safely with retries
def safe_open_file(file_path, retries=5, delay=2):
    for attempt in range(retries):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except PermissionError as e:
            print(f"Permission denied: {file_path}. Retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
            time.sleep(delay)
    raise PermissionError(f"Failed to access the file after {retries} retries: {file_path}")

# Function to parse JSON to CSV with backup
def parse_json_to_csv(json_file_path, primary_csv_path, backup_csv_dir):
    data = safe_open_file(json_file_path)

    contracts = {}

    for message in data.get('messages', []):
        if message.get('embeds'):
            for embed in message['embeds']:
                if any(title in embed.get('title', '') for title in [
                    "Bullish Bonding",
                    "Top 10 SOLANA Bullish Bonding",
                    "Top 10 SOLANA PF fomo calls",
                    "Top 10 SOLANA God Mode calls",
                    "Top 10 SOLANA Moon Finder calls"
                ]):
                    description = embed.get('description', '')
                    # Split the description into lines
                    lines = description.split('\n')

                    for line in lines:
                        # Check if the line contains a contract URL
                        contract_match = re.search(r'\[(.*?)\]\((?:https://www\.pump\.fun|https://dexscreener\.com/solana)/(.*?)\)', line)
                        if contract_match:
                            token_name, contract = contract_match.groups()

                            # Extract start mcap
                            start_mcap_match = re.search(r'@ (\d+\.?\d*(?:K|M))', line)
                            start_mcap = start_mcap_match.group(1) if start_mcap_match else ''

                            # Extract end mcap
                            end_mcap_match = re.search(r'➜ (\d+\.?\d*(?:K|M))', line)
                            end_mcap = end_mcap_match.group(1) if end_mcap_match else ''

                            # Extract profit multiples 
                            profit_multiples_match = re.search(r'Δ (\d+\.?\d*x)', line)
                            profit_multiples = profit_multiples_match.group(1) if profit_multiples_match else ''

                            # Convert K/M to actual numbers for comparison
                            def convert_to_float(value):
                                if not value:  # Handle empty strings
                                    return 0.0
                                if 'K' in value:
                                    return float(value.replace('K', '')) * 1000
                                elif 'M' in value:
                                    return float(value.replace('M', '')) * 1000000
                                else:
                                    return float(value)

                            start_mcap_num = convert_to_float(start_mcap)
                            end_mcap_num = convert_to_float(end_mcap)

                            # Use contract as key to avoid duplicates, update if newer or if no previous entry
                            if contract not in contracts or float(contracts[contract]['end_mcap']) < end_mcap_num:
                                contracts[contract] = {
                                    'Contract': contract,
                                    'Name': token_name,
                                    'Mcap': str(start_mcap_num),
                                    'HighestMcap': str(end_mcap_num),
                                    'Multiples': profit_multiples
                                }

    # Write to Primary CSV
    with open(primary_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Contract', 'Name', 'Mcap', 'HighestMcap', 'Multiples']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for contract in contracts.values():
            writer.writerow(contract)

    # Write to Backup CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_csv_path = os.path.join(backup_csv_dir, f"backup_{timestamp}.csv")
    with open(backup_csv_path, 'w', newline='', encoding='utf-8') as backup_csvfile:
        writer = csv.DictWriter(backup_csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for contract in contracts.values():
            writer.writerow(contract)
    print(f"Backup CSV created: {backup_csv_path}")

# Watchdog event handler for folder monitoring
class FileHandler(FileSystemEventHandler):
    def __init__(self, primary_save_dir, backup_save_dir):
        self.primary_save_dir = primary_save_dir
        self.backup_save_dir = backup_save_dir

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.json'):
            json_file_path = event.src_path
            csv_file_path = os.path.join(self.primary_save_dir, os.path.splitext(os.path.basename(json_file_path))[0] + '.csv')
            print(f"Detected new file: {json_file_path}")
            try:
                parse_json_to_csv(json_file_path, csv_file_path, self.backup_save_dir)
                print(f"CSV created: {csv_file_path}")
            except Exception as e:
                print(f"Error processing file {json_file_path}: {str(e)}")

# Function to monitor a folder
def watch_folder(folder_path, primary_save_dir, backup_save_dir):
    event_handler = FileHandler(primary_save_dir, backup_save_dir)
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()
    print(f"Watching folder: {folder_path}")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Main function to handle folder paths directly
def watch_folder_and_process(folder_path, primary_save_dir, backup_save_dir):
    print("Starting folder watcher...")
    watch_folder(folder_path, primary_save_dir, backup_save_dir)

# Uncomment to set folder paths and run automatically
watch_folder_and_process(
    'C:\\Users\\dant1\\Google Drive\\AG\\Code\\Channel Exports\\Top 10',
    'C:\\Users\\dant1\\Google Drive\\AG\\Code\\Channel Exports\\Top 10',
    'C:\\Users\\dant1\\Google Drive\\AG\\Code\\Exports Archive'
)
