import os
import json
import pandas as pd
import re
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

# Function to open a file safely with retries
def safe_open_file(file_path, retries=5, delay=2):
    for attempt in range(retries):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except PermissionError:
            print(f"Permission denied: {file_path}. Retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
            time.sleep(delay)
    raise PermissionError(f"Failed to access the file after {retries} retries: {file_path}")

# Function to clean and normalize text
def clean_data(text):
    if not text:
        return ""
    text = text.replace('`', '').strip()
    return text

# Function to parse Stats Creator field for Dev% and DevBal
def parse_stats_creator_field(field_value):
    field_value = clean_data(field_value)
    match = re.search(r'\(([\d.]+%)\s*\|\s*([\d.]+)\s*◎\)', field_value)
    if match:
        return match.group(1), match.group(2)
    return None, None

# Function to parse JSON and convert to CSV
def parse_json_to_csv(json_file_path, primary_csv_path, backup_csv_path):
    data = safe_open_file(json_file_path)

    contracts = []
    total_messages = len(data.get('messages', []))
    processed_messages = 0

    for message in data.get('messages', []):
        if 'embeds' in message and message['embeds']:
            embed = message['embeds'][0]
            if 'fields' in embed:
                stats_field = next((f for f in embed['fields'] if f['name'].startswith('Stats ')), None)
                if not stats_field:
                    continue

                # Extract contract from description
                contract_match = re.search(r'```([\w\d]+)```', embed.get('description', ''))
                contract = contract_match.group(1) if contract_match else ''

                # Extract timestamp
                timestamp = message['timestamp']

                # Extract stats fields
                stats_fields = {f['name']: f['value'] for f in embed['fields']}
                stats_value = stats_fields.get(stats_field['name'], '')
                mc = re.search(r'\*\*MC\*\*: `\$(\d{1,3}(?:,\d{3})*)`', stats_value)
                liq = re.search(r'\*\*Liq\*\*: `\$(\d{1,3}(?:,\d{3})*)`', stats_value)
                liq_percent = re.search(r'\*\*Liq\*\*:.*?\(?([\d.]+%)\)?', stats_value)
                b_ratio = re.search(r'\*\*B:\**\s*`([\d.]+%)`', stats_value)
                wallet_match = re.search(r'\*\*F\*\*: `(\d+)` \*\*KYC\*\*: `(\d+)` \*\*Unq\*\*: `(\d+)` \*\*SM\*\*: `(\d+)`', stats_value)

                # Extract Liq% value (no debug print)
                liq_percent_value = liq_percent.group(1) if liq_percent else ''

                # Creator stats
                creator_value = stats_fields.get('Stats Creator', '')
                ag = re.search(r'AG Score\*\*: `(\d+)/10`', creator_value)
                bundle = re.search(r'Bundled\*\*: `([\d.]+%)`', creator_value)
                funding_time = re.search(r'@ *(\d+[a-z]+)', creator_value)
                funding_source = re.search(r'\[(.*?)\]', creator_value)
                dev_percent, dev_balance = parse_stats_creator_field(creator_value)
                drained_match = re.search(r'Drained (\d+) of (\d+)', creator_value)
                fresh_deployer = 'Yes' if drained_match and drained_match.group(1) == '0' and drained_match.group(2) == '0' else 'No' if drained_match else 'No'
                drained = drained_match.group(1) if drained_match else '0'

                # Time to completion
                ttc_field = stats_fields.get('Time to completion', '')
                ttc = re.search(r'`(\d+)` seconds', ttc_field) if ttc_field else None
                ttc_value = ttc.group(1) if ttc else ''

                # Description
                desc = 'Yes' if stats_fields.get('Token Description', '') and stats_fields['Token Description'].strip() else 'No'

                # Build contract entry
                contract_entry = {
                    'Contract': contract,
                    'Timestamp': timestamp,
                    'Name': stats_field['name'].split('Stats ')[1],
                    'Mcap': mc.group(1).replace(',', '') if mc else '',
                    'Liq': liq.group(1).replace(',', '') if liq else '',
                    'Liq%': str(liq_percent_value),
                    'AG': ag.group(1) if ag else '',
                    'Bundle': bundle.group(1) if bundle else '',
                    'FundingTime': funding_time.group(1) if funding_time else '',
                    'FundingSource': funding_source.group(1) if funding_source else '',
                    'Dev%': dev_percent or '',
                    'DevBal': dev_balance or '',
                    'Links': 'Yes' if 'http' in stats_fields.get('Links', '') else 'No',
                    'F': wallet_match.group(1) if wallet_match else '0',
                    'KYC': wallet_match.group(2) if wallet_match else '0',
                    'Unq': wallet_match.group(3) if wallet_match else '0',
                    'SM': wallet_match.group(4) if wallet_match else '0',
                    'TTC': ttc_value,
                    'B-Ratio': b_ratio.group(1) if b_ratio else '',
                    'FreshDeployer': fresh_deployer,
                    'Drained': drained,
                    'Desc': desc
                }
                contracts.append(contract_entry)

        processed_messages += 1
        if processed_messages % 100 == 0 or processed_messages == total_messages:
            print(f"Progress: {processed_messages}/{total_messages} messages processed ({(processed_messages / total_messages) * 100:.2f}%)")

    # Define fieldnames for CSV
    fieldnames = [
        'Contract', 'Timestamp', 'Name', 'Mcap', 'Liq', 'Liq%', 'AG', 'Bundle',
        'FundingTime', 'FundingSource', 'Dev%', 'DevBal', 'Links', 'F', 'KYC', 'Unq', 'SM',
        'TTC', 'B-Ratio', 'FreshDeployer', 'Drained', 'Desc'
    ]
    df = pd.DataFrame(contracts)
    df = df.astype(str)  # Force all columns to string type
    df.to_csv(primary_csv_path, index=False)
    df.to_csv(backup_csv_path, index=False)

# Watchdog event handler
class FileHandler(FileSystemEventHandler):
    def __init__(self, watch_dir, primary_save_dir, backup_save_dir):
        self.watch_dir = watch_dir
        self.primary_save_dir = primary_save_dir
        self.backup_save_dir = backup_save_dir

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.json'):
            json_file_path = event.src_path
            base_name = os.path.splitext(os.path.basename(json_file_path))[0]  # e.g., 'BB-20250122-040001'
            
            # Use the JSON filename timestamp directly for CSV
            primary_csv_path = os.path.join(self.primary_save_dir, f"{base_name}.csv")
            backup_csv_path = os.path.join(self.backup_save_dir, f"{base_name}.csv")
            
            print(f"Detected new file: {json_file_path}")
            try:
                parse_json_to_csv(json_file_path, primary_csv_path, backup_csv_path)
                print(f"CSV created: {primary_csv_path}")
                print(f"Backup CSV created: {backup_csv_path}")
            except Exception as e:
                print(f"Error processing file {json_file_path}: {e}")

# Main function to watch folder
def watch_folder_and_process(folder_path, primary_save_dir, backup_save_dir):
    event_handler = FileHandler(folder_path, primary_save_dir, backup_save_dir)
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()
    print(f"Watching folder: {folder_path}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    watch_folder_and_process(
        'C:\\Users\\dant1\\Google Drive\\AG\\Code\\Channel Exports',
        'C:\\Users\\dant1\\Google Drive\\AG\\Code\\Channel Exports',
        'C:\\Users\\dant1\\Google Drive\\AG\\Code\\Exports Archive'
    )