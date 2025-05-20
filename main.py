from eda_service import EDAService
from cleanup import DataFrameCleaner
from loader import load_all_datasets
from IPython.display import display

try:
    df_inkooporderregels, df_ontvangstregels, df_relaties, df_feedback, df_suppliers = load_all_datasets()
except Exception:
    exit(1)



#  drop-lijst = alle kolommen behalve degene in rename_map
inkoop_columns_to_drop = {
    'OrNu',
    'Volgnummer',
    'ItCd',
    'Omschrijving',
    'GuLiIOR',
    'BronRegelGUID',
    'Upri',
    'Project',
    'RegelStatus',
    'QuUn',
    'TypeItem',
    'Opmerkingen',
    'Referentie',
    'ReferentieInkooprelatie',
    'VoorraadBijhouden',
    'StatusOrder',
    'Opmerking',
    'DsEx',
    'V1Cd',
    'Kostprijs',
    'ModifiedDate',
    'ModifiedDate1',
    'ModifiedDate2',
    'ModifiedDate3',
    'ModifiedDate4',
    'Definitief',
    'Regelbedrag',
    'WFS_ID',
    'WFS_ISR_ID',
    'WFS_DS_NR',
    'TotalValue',
    'AantalOntvangen',
    'Korting',
    'Verplichting',
    'Verantwoordelijke',
    'ItemCodeLeverancier',
    'sNr',
    'Gehad',
    'Red',
    'Naam'
}


# conversies = subset van dtype_mapping_inkoop die je behoudt (alleen de te hernoemen kolommen)
inkoop_columns_to_convert = {
    'Datum': 'datetime',
    'DatumToegezegd': 'datetime',
    'AfwijkendeAfleverdatum': 'datetime',
    'Vrijgegeven_op': 'datetime',
    'getDate': 'datetime',
    'CrId': 'int64',
}

# inkoop_rename_map = {
#     "Naam": "SupplierName",
#     "DatumInkooporder": "OrderDate",
#     "AfwijkendeAfleverdatum": "AdjustedDeliveryDate",
#     "DatumToegezegd": "DatumToegezegd"
# }


# Reiniging uitvoeren
cleaner = DataFrameCleaner(df_inkooporderregels, name="Inkooporderregels")

cleaner.drop_columns(inkoop_columns_to_drop)
cleaner.apply_dtype_mapping(inkoop_columns_to_convert)
# cleaner.rename_columns(inkoop_rename_map)
cleaner.normalize_nones()
df_inkooporderregels = cleaner.get_cleaned_df()

# EDA uitvoeren
# eda = EDAService(df_inkooporderregels, name="Inkooporderregels")
# eda.run_step(1)



# relation_rename = {
#     "Naam": "Name",
#     "Geblokkeerd": "Blocked",
#     "DbId": "Id"
# }
# suppliers_to_drop = [
#     'BcCo', 'StraatHuisnr', 'PostcodeWoonplaats', 'Land', 
#     'TelNr', 'Email', 'IBAN', 'Btwnr', 'KvKnr', 'Betalingsvoorwaarde', 
#     'KredietLimiet', 'TempBlocked', 'BtwPlicht', 'Blocked', 'CreateDate', 
#     'ModifiedDate', 'IsCrediteur', 'Niet_tonen_in_inkooporderlijst', 
#     'AfwijkendEmail', 'sNr'
# ]
 
# suppliers_mapping = {
#     'CrId': 'int64',
#     'Naam': 'str'
# }

# suppliers_cleaner = DataFrameCleaner(df_suppliers, name="df_suppliers")
# suppliers_cleaner.drop_columns(suppliers_to_drop)
# suppliers_cleaner.apply_dtype_mapping(suppliers_mapping)
# # relation_cleaner.rename_columns(relation_rename)
# df_suppliers = suppliers_cleaner.get_cleaned_df()

# eda = EDAService(df_suppliers, name="df_suppliers")
# eda.run_step(1)
# print(df_inkooporderregels.columns.tolist())



# df_inkooporderregels = df_inkooporderregels.merge(df_suppliers[['CrId', 'Naam']], on='CrId', how='left')


# display(df_suppliers.head())

display(df_inkooporderregels.head())