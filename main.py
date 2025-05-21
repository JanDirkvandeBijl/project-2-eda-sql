# -----------------------------
# Imports and Initial Setup
# -----------------------------
import pandas as pd
from eda_service import EDAService
from cleanup import DataFrameCleaner
from loader import load_all_datasets
from ui import UI  # Assuming UI is in a file named ui.py

# -----------------------------
# Loading Datasets
# -----------------------------
try:
    df_inkooporderregels, df_ontvangstregels, df_relaties, df_feedback, df_suppliers = load_all_datasets()
except Exception:
    exit(1)

# -----------------------------
# Constants and Configurations
# -----------------------------
relevant_columns_inkoop = ['GuLiIOR', 'Datum', 'DatumToegezegd', 'AfwijkendeAfleverdatum', 'Naam', 'BronRegelGUID', 'QuUn', 'OrNu']
relevant_columns_ontvangst = ['BronregelGuid', 'Datum', 'AantalOntvangen', 'Status_regel', 'Itemcode', 'Naam']

inkoop_columns_to_convert = {
    'Datum': 'datetime',
    'DatumToegezegd': 'datetime',
    'AfwijkendeAfleverdatum': 'datetime',
    'Vrijgegeven_op': 'datetime',
    'getDate': 'datetime',
    'Naam': 'str'
}

ontvangst_columns_to_convert = {
    'Datum': 'datetime'
}

years_to_exclude = [2021, 2022]

# -----------------------------
# Cleaning and Preparation
# -----------------------------
cleaner_inkoop = DataFrameCleaner(df_inkooporderregels, name="df_inkooporderregels")
cleaner_inkoop.apply_dtype_mapping(inkoop_columns_to_convert)
df_inkooporderregels_clean = cleaner_inkoop.get_cleaned_df()[relevant_columns_inkoop].copy()

cleaner_ontvangst = DataFrameCleaner(df_ontvangstregels, name="df_ontvangstregels")
cleaner_ontvangst.apply_dtype_mapping(ontvangst_columns_to_convert)
df_ontvangstregels_clean = cleaner_ontvangst.get_cleaned_df()[relevant_columns_ontvangst].copy()

print("Number of rows with empty BronRegelGUID:", df_inkooporderregels_clean['BronRegelGUID'].isna().sum())

# -----------------------------
# Deriving Expected Delivery Dates
# -----------------------------
df_inkooporderregels_clean['ExpectedDeliveryDate'] = df_inkooporderregels_clean['AfwijkendeAfleverdatum'].combine_first(
    df_inkooporderregels_clean['DatumToegezegd']
)
df_inkooporderregels_clean.drop(columns=['AfwijkendeAfleverdatum', 'DatumToegezegd'], inplace=True)

# -----------------------------
# Helper: Delivery Analysis
# -----------------------------
def analyse_leveringen(df_subset, delivery_counts, total_received):
    df_subset = df_subset.copy()
    df_subset['DeliveryCount'] = df_subset['GuLiIOR'].map(delivery_counts).fillna(0).astype(int)
    df_subset['TotalReceived'] = df_subset['GuLiIOR'].map(total_received).fillna(0).astype(float)
    df_subset['QuUn'] = df_subset['QuUn'].fillna(0).astype(float)
    df_subset['FullyDelivered'] = df_subset['TotalReceived'] >= df_subset['QuUn']
    return df_subset

# -----------------------------
# Delivery Stats Preparation
# -----------------------------
delivery_counts = df_ontvangstregels_clean['BronregelGuid'].value_counts()
total_received = df_ontvangstregels_clean.groupby('BronregelGuid')['AantalOntvangen'].sum()

# -----------------------------
# Items Without Expected Delivery Date
# -----------------------------
items_without_date = df_inkooporderregels_clean[df_inkooporderregels_clean['ExpectedDeliveryDate'].isna()].copy()
items_without_date = analyse_leveringen(items_without_date, delivery_counts, total_received)

missing_total = len(items_without_date)
missing_no_delivery = (items_without_date['DeliveryCount'] == 0).sum()
fully_delivered_missing = items_without_date['FullyDelivered'].sum()

print(f"Percentage without expected delivery date: {(missing_total/len(df_inkooporderregels_clean) * 100):.2f}%")
print(f"Without delivery: {missing_no_delivery} ({(missing_no_delivery / missing_total) * 100:.2f}%)")
print(f"Fully delivered without delivery date: {fully_delivered_missing} ({(fully_delivered_missing / missing_total) * 100:.2f}%)")

# -----------------------------
# Items With Expected Delivery Date
# -----------------------------
items_with_date = df_inkooporderregels_clean[df_inkooporderregels_clean['ExpectedDeliveryDate'].notna()].copy()
items_with_date = analyse_leveringen(items_with_date, delivery_counts, total_received)

valid_total = len(items_with_date)
valid_no_delivery = (items_with_date['DeliveryCount'] == 0).sum()
fully_delivered_valid = items_with_date['FullyDelivered'].sum()

print(f"With expected delivery date: {valid_total}, without deliveries: {valid_no_delivery} ({(valid_no_delivery / valid_total) * 100:.2f}%)")
print(f"Fully delivered with expected date: {fully_delivered_valid} ({(fully_delivered_valid / valid_total) * 100:.2f}%)")

# -----------------------------
# Analysis: Missing Delivery Dates by Year
# -----------------------------
items_without_date['OrderYear'] = items_without_date['Datum'].dt.year
missing_per_year = items_without_date['OrderYear'].value_counts().sort_index()
missing_perc_per_year = (missing_per_year / missing_total * 100).round(2)

missing_summary = pd.DataFrame({
    'MissingCount': missing_per_year,
    'Percentage': missing_perc_per_year.map(lambda x: f"{x:.2f}%")
})

print("\nMissing delivery dates per year:")
print(missing_summary)

# -----------------------------
# Exclude Older Years
# -----------------------------
items_without_date = items_without_date[~items_without_date['Datum'].dt.year.isin(years_to_exclude)].copy()
items_with_date = items_with_date[~items_with_date['Datum'].dt.year.isin(years_to_exclude)].copy()

# -----------------------------
# Final Enrichment for UI
# -----------------------------
print(df_ontvangstregels_clean.info())
items_with_date['DeliveryDate'] = items_with_date['GuLiIOR'].map(
    df_ontvangstregels_clean.groupby('BronregelGuid')['Datum'].max()
)

missing_delivery_date_count = items_with_date['DeliveryDate'].isna().sum()
total_items = len(items_with_date)
print(
    f"Items with expected delivery date: {total_items}, without actual delivery date: {missing_delivery_date_count} "
    f"({(missing_delivery_date_count / total_items) * 100:.2f}%)"
)

# 2. Filter only rows with valid dates
mask = items_with_date['DeliveryDate'].notna() & items_with_date['ExpectedDeliveryDate'].notna()

# 3. Calculate delay where possible
items_with_date.loc[mask, 'DeliveryDelay'] = (
    items_with_date.loc[mask, 'DeliveryDate'] - items_with_date.loc[mask, 'ExpectedDeliveryDate']
).dt.days
print("Number of early deliveries:", (items_with_date['DeliveryDelay'] < 0).sum())
print("Number of on-time deliveries:", (items_with_date['DeliveryDelay'] == 0).sum())
print("Number of late deliveries:", (items_with_date['DeliveryDelay'] > 0).sum())

print(items_with_date.info())

# -----------------------------
# Interactive UI
# -----------------------------
ui = UI(items_with_date)
ui.year_selection()
ui.supplier_selection()
ui.show_date_analysis()
