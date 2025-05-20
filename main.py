import pandas as pd
import numpy as np
import requests
from eda_service import EDAService
from cleanup import DataFrameCleaner

def load_nested_json(url):
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict):
        return pd.DataFrame(data.values())
    elif isinstance(data, list):
        return pd.DataFrame(data)
    else:
        raise ValueError("Unsupported JSON structure")

# URLs of the datasets
url_inkooporderregels = "http://app-wfs-01:5100/F/Inkooporderregels_All.json"
url_ontvangstregels = "http://app-wfs-01:5100/F/Ontvangstregels.json"
url_relaties = "http://app-wfs-01:5100/F/Relaties.json"
url_feedback = "http://app-wfs-01:5100/F/FeedbackLeveranciers.json"

try:
    df_inkooporderregels = load_nested_json(url_inkooporderregels)
    df_ontvangstregels = load_nested_json(url_ontvangstregels)
    df_relaties = load_nested_json(url_relaties)
    df_feedback = load_nested_json(url_feedback)
except Exception as e:
    print(f"Error loading JSON data: {e}")
    exit(1)

# Optioneel: definieer een mapping per kolom voor het casten van datatypes
dtype_mapping_inkoop = {
    'DatumInkooporder': 'datetime',
    'DatumLevering': 'datetime',
    'Aantal': 'numeric',
    'ArtikelCode': 'str',
    'Goedgekeurd': 'bool'
}

# Reinig de DataFrame met opgegeven type conversies
# cleaner = DataFrameCleaner(df_inkooporderregels, name="Inkooporderregels")
# cleaner.apply_dtype_mapping(dtype_mapping_inkoop)
# df_inkooporderregels = cleaner.get_cleaned_df()

# Dictionary of step names for reference
step_names = {
    1: "Structure Overview",
    2: "Missing Values (count)",
    3: "Null Percentage",
    4: "Duplicate Rows",
    5: "Numeric Summary",
    6: "Numeric Ranges",
    7: "Categorical Summary",
    8: "Correlation Matrix"
}

# Voer een specifieke EDA stap uit op de gereinigde DataFrame
eda = EDAService(df_inkooporderregels, name="Inkooporderregels")
eda.run_step(1)
