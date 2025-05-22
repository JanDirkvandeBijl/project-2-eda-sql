# -----------------------------
# Imports and Initial Setup
# -----------------------------
import pandas as pd
from eda_service import EDAService
from cleanup import DataFrameCleaner
from loader import load_all_datasets
from ui import UI
from scipy.stats import chi2_contingency

# -----------------------------
# Load Datasets
# -----------------------------
try:
    df_inkooporderregels, df_ontvangstregels, df_relaties, df_feedback, df_suppliers = load_all_datasets()
except Exception:
    exit(1)

# -----------------------------
# Configuration
# -----------------------------
relevant_columns_inkoop = [
    'GuLiIOR', 'Datum', 'DatumToegezegd', 'AfwijkendeAfleverdatum',
    'Naam', 'BronRegelGUID', 'QuUn', 'OrNu', 'DsEx', 'StatusOrder', 'Verantwoordelijke'
]
relevant_columns_ontvangst = [
    'BronregelGuid', 'Datum', 'AantalOntvangen', 'Status_regel', 'Itemcode', 'Naam'
]

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
# Cleaning
# -----------------------------
cleaner_inkoop = DataFrameCleaner(df_inkooporderregels, name="df_inkooporderregels")
cleaner_inkoop.apply_dtype_mapping(inkoop_columns_to_convert)
df_inkooporderregels_clean = cleaner_inkoop.get_cleaned_df()[relevant_columns_inkoop].copy()

cleaner_ontvangst = DataFrameCleaner(df_ontvangstregels, name="df_ontvangstregels")
cleaner_ontvangst.apply_dtype_mapping(ontvangst_columns_to_convert)
df_ontvangstregels_clean = cleaner_ontvangst.get_cleaned_df()[relevant_columns_ontvangst].copy()

# -----------------------------
# Filter: remove irrelevant rows
# -----------------------------
# Hier verwijderen we de order regels waarvan standaard geen verzending wordt ingvuld of deze toch niet relevant is
df_inkooporderregels_clean = df_inkooporderregels_clean[df_inkooporderregels_clean['DsEx'] != 'KVERZEND'].copy()

# -----------------------------
# Determine Expected Delivery Date
# -----------------------------
# Bepaal de verwachte leverdatum per regel:
# Gebruik 'AfwijkendeAfleverdatum' als primaire bron, en val terug op 'DatumToegezegd' indien nodig.
# Voor de duidelijkheid dit is de datum waarop een order geleverd zou moeten zijn
df_inkooporderregels_clean['ExpectedDeliveryDate'] = df_inkooporderregels_clean['AfwijkendeAfleverdatum'].combine_first(
    df_inkooporderregels_clean['DatumToegezegd']
)
# Verwijder de kollommen die we nu niet meer nodig hebben
df_inkooporderregels_clean.drop(columns=['AfwijkendeAfleverdatum', 'DatumToegezegd'], inplace=True)

# Filter regels:
# - Alleen regels behouden waar zowel 'Datum' (orderdatum) als 'ExpectedDeliveryDate' gevuld is
# - Alleen regels behouden waar de verwachte leverdatum op of ná de orderdatum ligt
#   (levering vóór bestelling is niet logisch, dus die regels worden verwijderd)
df_inkooporderregels_clean = df_inkooporderregels_clean[
    df_inkooporderregels_clean['ExpectedDeliveryDate'].notna() &  # ExpectedDeliveryDate moet ingevuld zijn
    df_inkooporderregels_clean['Datum'].notna() &                 # Orderdatum moet ingevuld zijn
    (df_inkooporderregels_clean['ExpectedDeliveryDate'] >= df_inkooporderregels_clean['Datum'])  # Geen leverdatum vóór orderdatum
].copy()

# Determine max expected date per order 
# Dit is de datum waarop de laatste order regel binnen zou moeten zijn en dus de uiteindelijke leverdatum
latest_expected_per_order = df_inkooporderregels_clean.groupby('OrNu')['ExpectedDeliveryDate'].max()

# Add to dataframe
df_inkooporderregels_clean['OrderDeliveryDate'] = df_inkooporderregels_clean['OrNu'].map(latest_expected_per_order)
df_inkooporderregels_clean['OrderDeliveryDate'] = df_inkooporderregels_clean['OrderDeliveryDate'].dt.tz_localize(None)
df_inkooporderregels_clean['Datum'] = df_inkooporderregels_clean['Datum'].dt.tz_localize(None)

# -----------------------------
# Delivery Data Preparation
# -----------------------------

# Tel per regel-GUID hoe vaak er een levering op plaatsvond (meerdere leveringen mogelijk)
delivery_counts = df_ontvangstregels_clean['BronregelGuid'].value_counts()

# Bepaal het totaal aantal ontvangen stuks per regel-GUID
total_received = df_ontvangstregels_clean.groupby('BronregelGuid')['AantalOntvangen'].sum()

# Analyseer per inkoopregel of en hoeveel er geleverd is
def analyse_leveringen(df_subset, delivery_counts, total_received):
    df_subset = df_subset.copy()

    # Aantal keer dat er op deze regel iets is geleverd
    df_subset['DeliveryCount'] = df_subset['GuLiIOR'].map(delivery_counts).fillna(0).astype(int)

    # Totaal aantal ontvangen eenheden voor deze regel
    df_subset['TotalReceived'] = df_subset['GuLiIOR'].map(total_received).fillna(0).astype(float)

    # Zorg dat QuUn (besteld aantal) niet NaN is
    df_subset['QuUn'] = df_subset['QuUn'].fillna(0).astype(float)

    # Markeer of alles volledig is geleverd
    df_subset['FullyDelivered'] = df_subset['TotalReceived'] >= df_subset['QuUn']

    return df_subset

# -----------------------------
# Delivery Analysis
# -----------------------------

# Pas leveringsanalyse toe op alle regels met verwachte leverdatum
df_inkooporderregels_clean = analyse_leveringen(df_inkooporderregels_clean, delivery_counts, total_received)

# -----------------------------
# Calculate Delivery Delay
# -----------------------------

# Bepaal per regel de laatste bekende leverdatum op basis van ontvangstregels
df_inkooporderregels_clean['DeliveryDate'] = df_inkooporderregels_clean['GuLiIOR'].map(
    df_ontvangstregels_clean.groupby('BronregelGuid')['Datum'].max()
)

# Bereken afwijking tussen werkelijke en verwachte leverdatum (alleen waar beide datums beschikbaar zijn)
mask = df_inkooporderregels_clean['DeliveryDate'].notna() & df_inkooporderregels_clean['ExpectedDeliveryDate'].notna()
df_inkooporderregels_clean.loc[mask, 'DeliveryDelay'] = (
    df_inkooporderregels_clean.loc[mask, 'DeliveryDate'] - df_inkooporderregels_clean.loc[mask, 'ExpectedDeliveryDate']
).dt.days



# -----------------------------
# Optional: Hook up to UI
# -----------------------------
ui = UI(df_inkooporderregels_clean)
ui.year_selection()
ui.supplier_selection()
ui.show_date_analysis()

