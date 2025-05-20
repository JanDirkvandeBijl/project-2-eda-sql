from eda_service import EDAService
from cleanup import DataFrameCleaner
from loader import load_all_datasets
import pandas as pd

try:
    df_inkooporderregels, df_ontvangstregels, df_relaties, df_feedback, df_suppliers = load_all_datasets()
except Exception:
    exit(1)


print(len(df_inkooporderregels))
# Define the columns you want to keep (relevant columns)
# print(df_inkooporderregels.columns)
relevant_columns_inkoop = [
    'GuLiIOR', 'Datum', 'DatumToegezegd', 'AfwijkendeAfleverdatum', 'Naam'
]
# print(df_ontvangstregels.columns)
relevant_columns_ontvangst = [
    'BronregelGuid', 'Datum', 'TotaalOntvangen', 'NogTeOntvangen', 'Status_regel', 'Itemcode', 'Naam'
]

# Apply dtype conversions
inkoop_columns_to_convert = {
    'Datum': 'datetime', 
    'DatumToegezegd': 'datetime', 
    'AfwijkendeAfleverdatum': 'datetime', 
    'Vrijgegeven_op': 'datetime', 
    'getDate': 'datetime', 
    'Naam': 'str'
}

# Clean data for df_inkooporderregels
cleaner = DataFrameCleaner(df_inkooporderregels, name="df_inkooporderregels")
cleaner.apply_dtype_mapping(inkoop_columns_to_convert)  # Apply dtype conversions
df_inkooporderregels_clean = cleaner.get_cleaned_df()[relevant_columns_inkoop]

# Clean data for df_ontvangstregels
# cleaner2 = DataFrameCleaner(df_ontvangstregels, name="df_ontvangstregels")
# df_ontvangstregels_clean = cleaner2.get_cleaned_df()[relevant_columns_ontvangst]
df_ontvangstregels_clean = df_ontvangstregels

# Optionally, run the EDA service (unchanged part)
# eda = EDAService(df_ontvangstregels_clean, name="df_ontvangstregels")
# eda.run_step(1)

# Merge df_inkooporderregels_clean with df_ontvangstregels_clean on 'GuLiIOR' and 'BronregelGuid'
merged_df = pd.merge(df_inkooporderregels_clean, df_ontvangstregels_clean, 
                     left_on=['GuLiIOR'], right_on=['BronregelGuid'], how='left')
print(merged_df[['GuLiIOR', 'BronregelGuid', 'TotaalOntvangen']].head())
# Add the total deliveries column to df_inkooporderregels_clean
df_inkooporderregels_clean['TotalDeliveries'] = merged_df.groupby('GuLiIOR')['BronregelGuid'].transform('count')

# Get the most recent delivery date for each GuLiIOR from df_ontvangstregels_clean
latest_delivery_date = df_ontvangstregels_clean.groupby('BronregelGuid')['Datum'].max()

# Merge the most recent delivery date back into df_inkooporderregels_clean
df_inkooporderregels_clean['DeliveryDate'] = df_inkooporderregels_clean['GuLiIOR'].map(latest_delivery_date)
print(len(df_inkooporderregels_clean))

# Filter the rows where 'DeliveryDate' is NaT and 'TotalDeliveries' is 0
no_deliveries = df_inkooporderregels_clean[(df_inkooporderregels_clean['DeliveryDate'].isna()) & 
                                            (df_inkooporderregels_clean['TotalDeliveries'] == 0)]

# Print the first few rows
# print(len(no_deliveries))
# print(no_deliveries.head())

# Import necessary UI class and other dependencies
from ui import UI  # Assuming UI is in a file named `ui.py`
import pandas as pd

# Create the UI instance
ui = UI(df_inkooporderregels_clean)

# Select year for analysis
ui.year_selection()  # Call the year selection method

# Select suppliers for analysis
ui.supplier_selection()  # Call the supplier selection method

# Display the analysis and plot based on the selected year and suppliers
ui.show_date_analysis()  # Display the analysis and plot based on selected year and suppliers