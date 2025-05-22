# -----------------------------
# Imports and Initial Setup
# -----------------------------
import pandas as pd
from eda_service import EDAService
from cleanup import DataFrameCleaner
from loader import load_all_datasets
from ui import UI  

# -----------------------------
# Loading Datasets
# -----------------------------
try:
    df_inkooporderregels, df_ontvangstregels, df_relaties, df_feedback, df_suppliers = load_all_datasets()
except Exception:
    exit(1)
    
# print(df_inkooporderregels.columns)

# totaal = len(df_inkooporderregels)
# uniek = df_inkooporderregels['ItCd'].nunique(dropna=True)
# leeg = df_inkooporderregels['ItCd'].isna().sum()
# print(f"{'ItCd'}:")
# print(f"  Unieke waarden: {uniek}")
# print(f"  Lege (NaN) waarden: {leeg}")
# print(f"  Gevulde waarden: {totaal - leeg}\n")

# item_counts = df_inkooporderregels['ItCd'].value_counts()
# # Filter op alleen items die meer dan 5 keer voorkomen
# items_meer_dan_5 = item_counts[item_counts > 5]

# print(f"Aantal unieke ItCd's die meer dan 5 keer voorkomen: {len(items_meer_dan_5)}")
# print(items_meer_dan_5)
# -----------------------------
# Constants and Configurations
# -----------------------------
# This are the columns that I want to keep for the analysis
relevant_columns_inkoop = ['GuLiIOR', 'Datum', 'DatumToegezegd', 'AfwijkendeAfleverdatum', 'Naam', 'BronRegelGUID', 'QuUn', 'OrNu', 'DsEx']
relevant_columns_ontvangst = ['BronregelGuid', 'Datum', 'AantalOntvangen', 'Status_regel', 'Itemcode', 'Naam']

# These are the columns that I want to convert to their valid types
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

# -----------------------------
# Cleaning and Preparation
# -----------------------------
cleaner_inkoop = DataFrameCleaner(df_inkooporderregels, name="df_inkooporderregels")
cleaner_inkoop.apply_dtype_mapping(inkoop_columns_to_convert)
df_inkooporderregels_clean = cleaner_inkoop.get_cleaned_df()[relevant_columns_inkoop].copy()

cleaner_ontvangst = DataFrameCleaner(df_ontvangstregels, name="df_ontvangstregels")
cleaner_ontvangst.apply_dtype_mapping(ontvangst_columns_to_convert)
df_ontvangstregels_clean = cleaner_ontvangst.get_cleaned_df()[relevant_columns_ontvangst].copy()

df_inkooporderregels_clean = df_inkooporderregels_clean[df_inkooporderregels_clean['DsEx'] != 'KVERZEND'].copy()


# df_inkooporderregels_clean['Datum'] = df_inkooporderregels_clean['Datum'].dt.tz_localize(None)
# df_inkooporderregels_clean = df_inkooporderregels_clean[df_inkooporderregels_clean['Datum'] >= pd.Timestamp('2023-01-01')].copy()



# We hebben 13741 unieke orders

# Gemiddelde aantal items per order
# 

# Per leverancier
# Aantal leveringen
# aantal leveringen te vroeg, op tijd en te laat, niet geleverd
# Performance over time adhv degene hier net boven



# Per medewerker (later niet in presentatie)
# Aantal orders per maand
# Order waarde per maand



# TODO: Kijken of datum toegezegd nu wel altijd gevuld is maar misschien onder een ander item
all_orders = df_inkooporderregels_clean.groupby("OrNu")
all_orders_list = list(all_orders)
print(f"Complete order amount: {len(all_orders_list)}")
# Eerste groep: tuple van (OrNu-waarde, DataFrame)
first_order_id, first_order_df = all_orders_list[0]
# print(f"Ordernummer: {first_order_id}")
# print(first_order_df)

# -----------------------------
# Deriving Expected Delivery Dates
# -----------------------------
# Determine the expected delivery date per order line:
# Use 'AfwijkendeAfleverdatum' as the primary field; fall back to 'DatumToegezegd' if it's missing.
df_inkooporderregels_clean['ExpectedDeliveryDate'] = df_inkooporderregels_clean['AfwijkendeAfleverdatum'].combine_first(
    df_inkooporderregels_clean['DatumToegezegd']
)


df_inkooporderregels_clean = df_inkooporderregels_clean[
    (df_inkooporderregels_clean['ExpectedDeliveryDate'].notna()) &
    (df_inkooporderregels_clean['Datum'].notna()) &
    ((df_inkooporderregels_clean['ExpectedDeliveryDate'] - df_inkooporderregels_clean['Datum']).dt.days <= 1)
].copy()

# Compute the latest expected delivery date per order (OrNu).
# This represents the overall delivery deadline for the full order across all its lines.
latest_expected_per_order = (
    df_inkooporderregels_clean
    .groupby('OrNu')['ExpectedDeliveryDate']
    .max()
)

# Add a new column to each line with the latest expected delivery date for its full order.
df_inkooporderregels_clean['OrderDeliveryDate'] = df_inkooporderregels_clean['OrNu'].map(latest_expected_per_order)
df_inkooporderregels_clean['OrderDeliveryDate'] = df_inkooporderregels_clean['OrderDeliveryDate'].dt.tz_localize(None)
df_inkooporderregels_clean['Datum'] = df_inkooporderregels_clean['Datum'].dt.tz_localize(None)

mask = (
    df_inkooporderregels_clean['OrderDeliveryDate'].notna() &
    df_inkooporderregels_clean['Datum'].notna() &
    (df_inkooporderregels_clean['OrderDeliveryDate'] < df_inkooporderregels_clean['Datum'])
)

# Bekijk aantal en toon eventueel voorbeeldregels
aantal_fout = mask.sum()
print(f"Aantal regels waarbij OrderDeliveryDate vóór de orderdatum ligt: {aantal_fout}")

if aantal_fout > 0:
    print(df_inkooporderregels_clean.loc[mask, ['OrNu', 'Datum', 'OrderDeliveryDate', 'ExpectedDeliveryDate']].head(10))


# Nieuw: toon regels zonder ExpectedDeliveryDate
missing_expected_mask = df_inkooporderregels_clean['ExpectedDeliveryDate'].isna()
aantal_missing = missing_expected_mask.sum()
print(f"\nAantal regels zonder ExpectedDeliveryDate: {aantal_missing}")

# if aantal_missing > 0:
#     print("\nVoorbeeldregels zonder ExpectedDeliveryDate:")
#     print(df_inkooporderregels_clean.loc[missing_expected_mask, ['OrNu', 'Datum', 'AfwijkendeAfleverdatum', 'DatumToegezegd']].head(10))


# Get rid of the columns that are not needed anymore
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

# print(f"Percentage without expected delivery date: {(missing_total/len(df_inkooporderregels_clean) * 100):.2f}%")
# print(f"Without delivery: {missing_no_delivery} ({(missing_no_delivery / missing_total) * 100:.2f}%)")
# print(f"Fully delivered without delivery date: {fully_delivered_missing} ({(fully_delivered_missing / missing_total) * 100:.2f}%)")

# -----------------------------
# Items With Expected Delivery Date
# -----------------------------
items_with_date = df_inkooporderregels_clean[df_inkooporderregels_clean['ExpectedDeliveryDate'].notna()].copy()
items_with_date = analyse_leveringen(items_with_date, delivery_counts, total_received)

valid_total = len(items_with_date)
valid_no_delivery = (items_with_date['DeliveryCount'] == 0).sum()
fully_delivered_valid = items_with_date['FullyDelivered'].sum()

# print(f"With expected delivery date: {valid_total}, without deliveries: {valid_no_delivery} ({(valid_no_delivery / valid_total) * 100:.2f}%)")
# print(f"Fully delivered with expected date: {fully_delivered_valid} ({(fully_delivered_valid / valid_total) * 100:.2f}%)")

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

# print("\nMissing delivery dates per year:")
# print(missing_summary)

def analyse_expected_delivery_date_consistency(df):
    grouped = df.groupby('OrNu')['ExpectedDeliveryDate']

    def classify(series):
        unique = series.dropna().unique()
        return 'all_missing' if len(unique) == 0 else ('consistent' if len(unique) == 1 else 'inconsistent')

    classifications = grouped.apply(classify)
    print("Consistency per order:\n", classifications.value_counts())

    inconsistent = classifications[classifications == 'inconsistent'].index
    if inconsistent.empty:
        print("Geen inconsistenties gevonden.")
        return

    verschil = (
        df[df['OrNu'].isin(inconsistent)]
        .groupby('OrNu')['ExpectedDeliveryDate']
        .agg(lambda x: (x.max() - x.min()).days if x.notna().all() else None)
        .dropna()
        .rename('VerschilInDagen')
        .sort_values(ascending=False)
    )

    print(f"\nAantal inconsistente orders: {len(verschil)}")
    print("\nTop 10 grootste verschillen in dagen:")
    print(verschil.head(10))


analyse_expected_delivery_date_consistency(items_with_date)
# -----------------------------
# Final Enrichment for UI
# -----------------------------
# print(df_ontvangstregels_clean.info())
items_with_date['DeliveryDate'] = items_with_date['GuLiIOR'].map(
    df_ontvangstregels_clean.groupby('BronregelGuid')['Datum'].max()
)




missing_delivery_date_count = items_with_date['DeliveryDate'].isna().sum()
total_items = len(items_with_date)
# print(
#     f"Items with expected delivery date: {total_items}, without actual delivery date: {missing_delivery_date_count} "
#     f"({(missing_delivery_date_count / total_items) * 100:.2f}%)"
# )

# 2. Filter only rows with valid dates
mask = items_with_date['DeliveryDate'].notna() & items_with_date['ExpectedDeliveryDate'].notna()

# 3. Calculate delay where possible
items_with_date.loc[mask, 'DeliveryDelay'] = (
    items_with_date.loc[mask, 'DeliveryDate'] - items_with_date.loc[mask, 'ExpectedDeliveryDate']
).dt.days
# print("Number of early deliveries:", (items_with_date['DeliveryDelay'] < 0).sum())
# print("Number of on-time deliveries:", (items_with_date['DeliveryDelay'] == 0).sum())
# print("Number of late deliveries:", (items_with_date['DeliveryDelay'] > 0).sum())


# -----------------------------
# Interactive UI
# -----------------------------
# ui = UI(items_with_date)
# ui.year_selection()
# ui.supplier_selection()
# ui.show_date_analysis()
