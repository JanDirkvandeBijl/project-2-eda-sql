import os
import json
import pandas as pd
import requests

# Lokale directory waar de JSON-bestanden worden opgeslagen
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

datasets = {
    "Inkooporderregels": ("http://10.11.10.104:5100/F/Inkooporderregels_All.json", "Inkooporderregels_All.json"),
    "Ontvangstregels": ("http://10.11.10.104:5100/F/Ontvangstregels.json", "Ontvangstregels.json"),
    "Relaties": ("http://10.11.10.104:5100/F/Relaties.json", "Relaties.json"),
    "FeedbackLeveranciers": ("http://10.11.10.104:5100/F/FeedbackLeveranciers.json", "FeedbackLeveranciers.json"),
    "Leveranciers": ("http://10.11.10.104:5100/F/Leveranciers.json", "Leveranciers.json")  # Added Leveranciers dataset
}

def download_if_missing(url: str, filename: str, log: bool = False):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        if log:
            print(f"Downloading {filename} from {url} ...")
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(response.json(), f, ensure_ascii=False)
            if log:
                print(f"Saved to {filepath}")
        except Exception as e:
            if log:
                print(f"Failed to download {filename}: {e}")
            raise
    else:
        if log:
            print(f"Using cached file: {filepath}")
    return filepath

def load_nested_json_file(filepath: str, log: bool = False):
    if log:
        print(f"Loading file: {filepath}")
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        return pd.DataFrame(data.values())
    elif isinstance(data, list):
        return pd.DataFrame(data)
    else:
        raise ValueError("Unsupported JSON structure")

def load_all_datasets(log: bool = False):
    try:
        file_inkoop = download_if_missing(*datasets["Inkooporderregels"], log=log)
        file_ontvangst = download_if_missing(*datasets["Ontvangstregels"], log=log)
        file_relaties = download_if_missing(*datasets["Relaties"], log=log)
        file_feedback = download_if_missing(*datasets["FeedbackLeveranciers"], log=log)
        file_leveranciers = download_if_missing(*datasets["Leveranciers"], log=log)  # Added Leveranciers download

        df_inkoop = load_nested_json_file(file_inkoop, log=log)
        df_ontvangst = load_nested_json_file(file_ontvangst, log=log)
        df_relaties = load_nested_json_file(file_relaties, log=log)
        df_feedback = load_nested_json_file(file_feedback, log=log)
        df_leveranciers = load_nested_json_file(file_leveranciers, log=log)  # Added Leveranciers DataFrame

        return df_inkoop, df_ontvangst, df_relaties, df_feedback, df_leveranciers  # Return Leveranciers dataframe
    except Exception as e:
        if log:
            print(f"Error loading datasets: {e}")
        raise
