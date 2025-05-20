import pandas as pd
import numpy as np

class DataFrameCleaner:
    def __init__(self, df: pd.DataFrame, name: str = "DataFrame", log_enabled: bool = False):
        """
        Maak een nieuwe cleaner voor een pandas DataFrame.

        Parameters:
        - df: De originele DataFrame die schoongemaakt moet worden.
        - name: Een optionele naam voor logging/prints.
        - log_enabled: Als True, worden logberichten geprint.
        """
        self.df = df.copy()
        self.name = name
        self.low_info_cols = []
        self.log_enabled = log_enabled

    def _log(self, message: str):
        if self.log_enabled:
            print(message)

    def drop_columns(self, columns: list):
        self._log(f"\n=== {self.name} — Dropping Specified Columns ===")

        existing_cols = [col for col in columns if col in self.df.columns]
        missing_cols = [col for col in columns if col not in self.df.columns]

        if existing_cols:
            self.df.drop(columns=existing_cols, inplace=True)
            self._log(f"Dropped columns: {', '.join(existing_cols)}")
        else:
            self._log("No columns to drop.")

        if missing_cols:
            self._log(f"Skipped (not found): {', '.join(missing_cols)}")

    def apply_dtype_mapping(self, mapping: dict = None):
        self._log(f"\n=== {self.name} — Applying Type Mappings ===")
        if mapping is None:
            self._log("No mapping provided.")
            return

        converted = []
        skipped = []
        failed = []

        for column, target_type in mapping.items():
            if column not in self.df.columns:
                skipped.append(column)
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
                converted.append((column, target_type))
            except Exception:
                failed.append(column)

        if converted:
            self._log("Converted columns:")
            for col, dtype in converted:
                self._log(f"  - {col}: {dtype}")

        if skipped:
            self._log(f"Skipped (not in DataFrame): {', '.join(skipped)}")

        if failed:
            self._log(f"Failed to convert: {', '.join(failed)}")

    def rename_columns(self, rename_map: dict):
        self._log(f"\n=== {self.name} — Renaming Columns ===")

        existing = {k: v for k, v in rename_map.items() if k in self.df.columns}
        missing = [k for k in rename_map if k not in self.df.columns]

        if existing:
            self.df.rename(columns=existing, inplace=True)
            self._log("Renamed columns:")
            for old, new in existing.items():
                self._log(f"  - {old} -> {new}")
        else:
            self._log("No columns were renamed.")

        if missing:
            self._log(f"Skipped (not found): {', '.join(missing)}")

    def normalize_nones(self):
        self._log(f"\n=== {self.name} — Replacing 'None'/'null' strings with NaN ===")
        self.df.replace(["None", "null"], pd.NA, inplace=True)

    def get_cleaned_df(self):
        return self.df
