import os
import json
import pandas as pd

# Define the folder containing the JSON-LD files
folder_path = 'v0/classes'  # update with your folder path

# Dictionary to store data where keys are file names (without extension) and values are dicts of key-value pairs
data = {}

# Iterate over all files in the folder
for filename in os.listdir(folder_path):
    if filename.endswith('.jsonld'):
        file_id = os.path.splitext(filename)[0]  # Remove extension, e.g. "C01" from "C01.jsonld"
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                json_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in file {filename}: {e}")
                continue

            # Filter out key-value pairs that start with 'xxx:'
            filtered = {}
            for key, value in json_data.items():
                if not key.startswith("xxx:"):
                    # # If the value is not a string, replace it with a placeholder
                    # if isinstance(value, list):
                    #     filtered[key] = str(value)[:15]
                    # elif isinstance(value, dict):
                    #     filtered[key] = str(value)[:15]
                    # else:
                    #     filtered[key] = value
                    filtered[key] = value
            data[file_id] = filtered

# Create a set of all keys found across all files
all_keys = set()
for file_dict in data.values():
    all_keys.update(file_dict.keys())

# Build a DataFrame where index is the keys (row names) and columns are file identifiers
df = pd.DataFrame(index=sorted(all_keys))

for file_id, kv in data.items():
    # Create a Series for this file, aligning it with the DataFrame index
    s = pd.Series(kv)
    df[file_id] = s

# Save the DataFrame to CSV
output_csv = 'known_fields.csv'
df.to_csv(output_csv)

print(f"CSV output written to {output_csv}")
