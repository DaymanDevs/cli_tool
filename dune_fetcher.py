import csv
from dune_client.client import DuneClient
from datetime import datetime
import os
from config import DATA_DIRECTORY  # Import DATA_DIRECTORY from config.py

# Initialize DuneClient with your API key
API_KEY = "h4ZLtm3ncY1JawdkTP42iGEzJrb2f5RY"
QUERY_ID = 4580261  # Query ID for MCAPS data

def fetch_and_save_dune_data(api_key, query_id, output_dir=DATA_DIRECTORY):
    """Fetch data from Dune Analytics and save to a timestamped CSV file."""
    try:
        # Initialize the Dune client
        dune = DuneClient(api_key)

        # Fetch the latest query result
        query_result = dune.get_latest_result(query_id)

        # Extract rows from the result
        rows = query_result.result.rows

        # Check if rows are available
        if not rows:
            print("No data available in the query result.")
            return

        # Extract the headers (keys of the first dictionary)
        headers = rows[0].keys()

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        filename = f"MCAPS-{timestamp}.csv"
        output_path = os.path.join(output_dir, filename)

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Write data to CSV
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        print(f"Data successfully written to {output_path}")

    except Exception as e:
        print(f"Error: {e}")

# Main script
if __name__ == "__main__":
    fetch_and_save_dune_data(API_KEY, QUERY_ID)