# -----------------------------
# Imports and Initial Setup
# -----------------------------
from eda_service import EDAService
from cleanup import DataFrameCleaner
from loader import load_all_datasets
import pandas as pd
from ui import UI  # Assuming UI is in a file named ui.py

# -----------------------------
# Loading Datasets
# -----------------------------
# Load all required datasets; exit on failure
try:
    df_inkooporderregels, df_ontvangstregels, df_relaties, df_feedback, df_suppliers = load_all_datasets()
except Exception:
    exit(1)

# -----------------------------
# Relevant Columns and Type Mappings
# -----------------------------
# Specify relevant columns for analysis and expected data types
relevant_columns_inkoop = ['GuLiIOR', 'Datum', 'DatumToegezegd', 'AfwijkendeAfleverdatum', 'Naam', 'BronRegelGUID', 'QuUn']
relevant_columns_ontvangst = ['BronregelGuid', 'Datum', 'AantalOntvangen', 'Status_regel', 'Itemcode', 'Naam']
inkoop_columns_to_convert = {
    'Datum': 'datetime',
    'DatumToegezegd': 'datetime',
    'AfwijkendeAfleverdatum': 'datetime',
    'Vrijgegeven_op': 'datetime',
    'getDate': 'datetime',
    'Naam': 'str'
}

# -----------------------------
# Cleaning and Preparation
# -----------------------------
# Clean purchase order lines
cleaner_inkoop = DataFrameCleaner(df_inkooporderregels, name="df_inkooporderregels")
cleaner_inkoop.apply_dtype_mapping(inkoop_columns_to_convert)
df_inkooporderregels_clean = cleaner_inkoop.get_cleaned_df()[relevant_columns_inkoop].copy()

# Clean delivery receipt lines
cleaner_ontvangst = DataFrameCleaner(df_ontvangstregels, name="df_ontvangstregels")
df_ontvangstregels_clean = cleaner_ontvangst.get_cleaned_df()[relevant_columns_ontvangst].copy()

# -----------------------------
# Deriving Expected Delivery Dates
# -----------------------------
# Resolve expected delivery date from override or original date
df_inkooporderregels_clean['ExpectedDeliveryDate'] = df_inkooporderregels_clean['AfwijkendeAfleverdatum'].combine_first(
    df_inkooporderregels_clean['DatumToegezegd']
)
df_inkooporderregels_clean.drop(columns=['AfwijkendeAfleverdatum', 'DatumToegezegd'], inplace=True)

# -----------------------------
# Analysis: Missing Delivery Dates
# -----------------------------
# Subset lines without expected delivery date
items_without_date = df_inkooporderregels_clean[df_inkooporderregels_clean['ExpectedDeliveryDate'].isna()].copy()

# Map number of deliveries per BronregelGuid to GuLiIOR
delivery_counts = df_ontvangstregels_clean['BronregelGuid'].value_counts()
items_without_date['DeliveryCount'] = items_without_date['GuLiIOR'].map(delivery_counts).fillna(0).astype(int)

# Logging stats
missing_total = len(items_without_date)

print(f"Percentage that doesnt have a delivery date: {(missing_total/len(df_inkooporderregels_clean) * 100)}")

missing_no_delivery = (items_without_date['DeliveryCount'] == 0).sum()
print(f"Items without expected delivery date: {missing_total}, of which have no deliveries: {missing_no_delivery} ({(missing_no_delivery / missing_total) * 100:.2f}%)")

# -----------------------------
# Analysis: Fully Delivered without Expected Date
# -----------------------------
# Sum all received quantities per BronregelGuid
total_received = df_ontvangstregels_clean.groupby('BronregelGuid')['AantalOntvangen'].sum()

# Map to items_without_date
items_without_date['TotalReceived'] = items_without_date['GuLiIOR'].map(total_received).fillna(0).astype(float)
items_without_date['QuUn'] = items_without_date['QuUn'].fillna(0).astype(float)

# Flag as fully delivered
items_without_date['FullyDelivered'] = items_without_date['TotalReceived'] >= items_without_date['QuUn']

# Report
fully_delivered_missing = items_without_date['FullyDelivered'].sum()
print(f"Items without expected delivery date: {missing_total}, fully delivered: {fully_delivered_missing} ({(fully_delivered_missing / missing_total) * 100:.2f}%)")

# -----------------------------
# Analysis: Valid Delivery Dates
# -----------------------------
# Subset lines with expected delivery date
items_with_date = df_inkooporderregels_clean[df_inkooporderregels_clean['ExpectedDeliveryDate'].notna()].copy()

# Map delivery counts again (already computed above)
items_with_date['DeliveryCount'] = items_with_date['GuLiIOR'].map(delivery_counts).fillna(0).astype(int)

# Logging stats
valid_total = len(items_with_date)
valid_no_delivery = (items_with_date['DeliveryCount'] == 0).sum()
print(f"Items with expected delivery date: {valid_total}, of which have no deliveries: {valid_no_delivery} ({(valid_no_delivery / valid_total) * 100:.2f}%)")

# -----------------------------
# Analysis: Fully Delivered with Expected Date
# -----------------------------
# Reuse total_received from above
items_with_date['TotalReceived'] = items_with_date['GuLiIOR'].map(total_received).fillna(0).astype(float)
items_with_date['QuUn'] = items_with_date['QuUn'].fillna(0).astype(float)

# Flag as fully delivered
items_with_date['FullyDelivered'] = items_with_date['TotalReceived'] >= items_with_date['QuUn']

# Report
fully_delivered_valid = items_with_date['FullyDelivered'].sum()
print(f"Items with expected delivery date: {valid_total}, fully delivered: {fully_delivered_valid} ({(fully_delivered_valid / valid_total) * 100:.2f}%)")


# -----------------------------
# Missing Delivery Dates by Year
# -----------------------------
# Extract year from original order date
items_without_date['OrderYear'] = items_without_date['Datum'].dt.year

# Count and percentage of missing delivery dates per year
missing_per_year = items_without_date['OrderYear'].value_counts().sort_index()
missing_perc_per_year = (missing_per_year / missing_total * 100).round(2)

# Combine into one DataFrame
missing_summary = pd.DataFrame({
    'MissingCount': missing_per_year,
    'Percentage': missing_perc_per_year.map(lambda x: f"{x:.2f}%")
})

# Print the combined result
print("\nMissing delivery dates per year:")
print(missing_summary)
# Missing delivery dates per year:
#            MissingCount Percentage
# OrderYear
# 2021               2339     71.53%
# 2022                638     19.51%
# 2023                122      3.73%
# 2024                123      3.76%
# 2025                 48      1.47%


# we can see that this issue is happening mostly in older data
# Actions
# 1 I will try to hunt down the reason why it still happens sometimes and try to fill them later 
# 2 I will remove the years 2021 and 2022 from this evaluation to minimize the impact of that since its older data this is fine for now -> maybe when i know the reason for action 1 i will add them back

# Define years to exclude
years_to_exclude = [2021, 2022]

# Filter items_without_date
items_without_date = items_without_date[~items_without_date['Datum'].dt.year.isin(years_to_exclude)].copy()

# Filter items_with_date
items_with_date = items_with_date[~items_with_date['Datum'].dt.year.isin(years_to_exclude)].copy()


# Now we will look into the supplier details and for now leave the items_without_date until these are fixed

unique_suppliers = items_with_date['Naam'].unique()
print(f"Unique suppliers {len(unique_suppliers)}")
# Result is: Unique suppliers 350

# Add latest delivery date per GuLiIOR (matching on BronregelGuid)
items_with_date['DeliveryDate'] = items_with_date['GuLiIOR'].map(
    df_ontvangstregels_clean.groupby('BronregelGuid')['Datum'].max()
)
missing_delivery_date_count = items_with_date['DeliveryDate'].isna().sum()
total_items = len(items_with_date)
print(
    f"Items with expected delivery date: {total_items}, without actual delivery date: {missing_delivery_date_count} "
    f"({(missing_delivery_date_count / total_items) * 100:.2f}%)"
)

print(items_with_date.columns)
# with pd.option_context('display.max_rows', None, 'display.max_columns', None):





# Create the UI instance
ui = UI(items_with_date)

# Select year for analysis
ui.year_selection()  # Call the year selection method

# Select suppliers for analysis
ui.supplier_selection()  # Call the supplier selection method

# Display the analysis and plot based on the selected year and suppliers
ui.show_date_analysis()  # Display the analysis and plot based on selected year and suppliers



