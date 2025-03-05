import pandas as pd
import os
import re

def load_and_combine_csv(directory):
    combined_data = {}
    channel_pattern = re.compile(r"^(.*?)-\d+")

    csv_files = sorted([f for f in os.listdir(directory) if f.endswith('.csv')])

    for file in csv_files:
        match = channel_pattern.match(file)
        if match:
            channel = match.group(1)
            df = pd.read_csv(os.path.join(directory, file))
            if channel in combined_data:
                combined_data[channel] = pd.concat([combined_data[channel], df], ignore_index=True)
            else:
                combined_data[channel] = df

    # Optional: Clean the data further if needed
    for channel, df in combined_data.items():
        df.drop_duplicates(inplace=True)

    return combined_data
