from eda_service import EDAService
from cleanup import DataFrameCleaner
from loader import load_all_datasets
import pandas as pd
from ui import UI  # Assuming UI is in a file named ui.py

# Load all required datasets
try:
    df_inkooporderregels, df_ontvangstregels, df_relaties, df_feedback, df_suppliers = load_all_datasets()
except Exception:
    exit(1)

# Define relevant columns to retain for analysis
relevant_columns_inkoop = [
    'GuLiIOR', 'Datum', 'DatumToegezegd', 'AfwijkendeAfleverdatum', 'Naam', 'BronRegelGUID'
]

relevant_columns_ontvangst = [
    'BronregelGuid', 'Datum', 'TotaalOntvangen', 'NogTeOntvangen', 'Status_regel', 'Itemcode', 'Naam'
]

# Define columns to convert to specific dtypes
inkoop_columns_to_convert = {
    'Datum': 'datetime',
    'DatumToegezegd': 'datetime',
    'AfwijkendeAfleverdatum': 'datetime',
    'Vrijgegeven_op': 'datetime',
    'getDate': 'datetime',
    'Naam': 'str'
}

# Clean and prepare df_inkooporderregels
cleaner = DataFrameCleaner(df_inkooporderregels, name="df_inkooporderregels")
cleaner.apply_dtype_mapping(inkoop_columns_to_convert)
df_inkooporderregels_clean = cleaner.get_cleaned_df()[relevant_columns_inkoop].copy()

# Clean and prepare df_ontvangstregels
cleaner2 = DataFrameCleaner(df_ontvangstregels, name="df_ontvangstregels")
df_ontvangstregels_clean = cleaner2.get_cleaned_df()[relevant_columns_ontvangst]

# --- Create unified delivery date ---

# 1. DatumToegezegd is the original promised delivery date and should not be changed.
# 2. AfwijkendeAfleverdatum is the override delivery date and may be updated.
# 3. ExpectedDeliveryDate is resolved from either of the two.
# 4. TODO: Handle cases where both are missing.

df_inkooporderregels_clean['ExpectedDeliveryDate'] = df_inkooporderregels_clean['AfwijkendeAfleverdatum'].combine_first(
    df_inkooporderregels_clean['DatumToegezegd']
)

# Remove the original date columns
df_inkooporderregels_clean.drop(columns=['AfwijkendeAfleverdatum', 'DatumToegezegd'], inplace=True)

# --- Identify faulty rows (missing expected delivery date) ---

# These records must be investigated
items_without_delivery_date = df_inkooporderregels_clean[
    df_inkooporderregels_clean['ExpectedDeliveryDate'].isna()
].copy()

# Group ontvangstregels by BronregelGuid and sum received quantities
delivery_sums = df_ontvangstregels_clean.groupby('BronregelGuid')['TotaalOntvangen'].sum()

# Map the delivery totals to items_without_delivery_date using GuLiIOR
items_without_delivery_date['Deliveries'] = items_without_delivery_date['GuLiIOR'].map(delivery_sums)

# Fill missing values with 0 for unmatched items
items_without_delivery_date['Deliveries'] = items_without_delivery_date['Deliveries'].fillna(0)

# --- Logging the issue scope ---

missing_total = len(items_without_delivery_date)
missing_with_no_delivery = (items_without_delivery_date['Deliveries'] == 0).sum()

print(
    "Items without expected delivery date: {}, of which have no deliveries: {} ({:.2f}%)".format(
        missing_total,
        missing_with_no_delivery,
        (missing_with_no_delivery / missing_total) * 100
    )
) 
# Result is: Items without expected delivery date: 3270, of which have no deliveries: 3235 (98.93%)
# Conclusion -> We will create a seperate visual for these record and investigate later how these happen most likely these are canceled orders



# Subset 3: Correct lines (ExpectedDeliveryDate is filled)
items_with_delivery_date = df_inkooporderregels_clean[df_inkooporderregels_clean['ExpectedDeliveryDate'].notna()].copy()





# # Optionally, run the EDA service (unchanged part)
# # eda = EDAService(df_inkooporderregels, name="df_inkooporderregels")
# # eda.run_step(1)

# # Merge df_inkooporderregels_clean with df_ontvangstregels_clean on 'GuLiIOR' and 'BronregelGuid'
# merged_df = pd.merge(df_inkooporderregels_clean, df_ontvangstregels_clean, 
#                      left_on=['GuLiIOR'], right_on=['BronregelGuid'], how='left')
# print(merged_df[['GuLiIOR', 'BronregelGuid', 'TotaalOntvangen']].head())
# # Add the total deliveries column to df_inkooporderregels_clean
# df_inkooporderregels_clean['TotalDeliveries'] = merged_df.groupby('GuLiIOR')['BronregelGuid'].transform('count')

# # Get the most recent delivery date for each GuLiIOR from df_ontvangstregels_clean
# latest_delivery_date = df_ontvangstregels_clean.groupby('BronregelGuid')['Datum'].max()

# # Merge the most recent delivery date back into df_inkooporderregels_clean
# df_inkooporderregels_clean['DeliveryDate'] = df_inkooporderregels_clean['GuLiIOR'].map(latest_delivery_date)
# print(len(df_inkooporderregels_clean))

# # Filter the rows where 'DeliveryDate' is NaT and 'TotalDeliveries' is 0
# no_deliveries = df_inkooporderregels_clean[(df_inkooporderregels_clean['DeliveryDate'].isna()) & 
#                                             (df_inkooporderregels_clean['TotalDeliveries'] == 0)]

# # Print the first few rows
# # print(len(no_deliveries))
# # print(no_deliveries.head())





# # Create the UI instance
# ui = UI(df_inkooporderregels_clean)

# # Select year for analysis
# ui.year_selection()  # Call the year selection method

# # Select suppliers for analysis
# ui.supplier_selection()  # Call the supplier selection method

# # Display the analysis and plot based on the selected year and suppliers
# ui.show_date_analysis()  # Display the analysis and plot based on selected year and suppliers






# Controleer of er geldige datums zijn
# if items_without_delivery_date['Datum'].notna().any():
#     # Vind de index van de rij met de hoogste Datum
#     idx = items_without_delivery_date['Datum'].idxmax()

#     print(f"Index met hoogste Datum: {idx}")
#     print(items_without_delivery_date.loc[idx])

#     # Haal de BronRegelGUID uit die rij
#     bronregel_id = items_without_delivery_date.loc[idx, 'BronRegelGUID']
#     print(f"BronRegelGUID van die rij: {bronregel_id}")

#     # Zoek de bijbehorende rij(en) in het originele DataFrame
#     item = df_inkooporderregels[df_inkooporderregels['BronRegelGUID'] == bronregel_id]

#     # Print het volledige item (alle kolommen, alle matches)
#     print("\nVolledige rij(en) uit df_inkooporderregels met deze BronRegelGUID:")
#     print(item.to_string(index=False))  # netjes zonder index
# else:
#     # Geen geldige datums aanwezig
#     aantal_leeg = items_without_delivery_date['ExpectedDeliveryDate'].isna().sum()
#     print(f"Aantal lege ExpectedDeliveryDate: {aantal_leeg}")

