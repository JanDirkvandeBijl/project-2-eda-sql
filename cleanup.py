import pandas as pd

class DataFrameCleaner:
    def __init__(self, df: pd.DataFrame, name: str = "DataFrame"):
        self.df = df.copy()
        self.name = name

    def apply_dtype_mapping(self, mapping: dict = None):
        # Purpose: Map specified columns to given dtypes explicitly
        print(f"\n=== {self.name} — Applying Type Mappings ===")
        if mapping is None:
            print("No mapping provided.")
            return

        for column, target_type in mapping.items():
            if column not in self.df.columns:
                print(f"Skipping '{column}': not in dataframe.")
                continue
            try:
                if target_type == 'datetime':
                    self.df[column] = pd.to_datetime(self.df[column], errors='coerce', utc=True)
                elif target_type == 'numeric':
                    self.df[column] = pd.to_numeric(self.df[column], errors='coerce')
                elif target_type == 'str':
                    self.df[column] = self.df[column].astype(str)
                elif target_type == 'bool':
                    self.df[column] = self.df[column].astype(bool)
                else:
                    self.df[column] = self.df[column].astype(target_type)
                print(f"Converted '{column}' to {target_type}")
            except Exception as e:
                print(f"Failed to convert '{column}' to {target_type}: {e}")

    def get_cleaned_df(self):
        return self.df
