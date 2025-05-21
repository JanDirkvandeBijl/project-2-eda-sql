import pandas as pd
import numpy as np

class DataFrameCleaner:
    def __init__(self, df: pd.DataFrame, name: str = "DataFrame", log_enabled: bool = False):
        """
        Initialize the cleaner using the input DataFrame directly (no copy).

        Parameters:
        - df: The input pandas DataFrame to clean (modified in-place).
        - name: Optional name used in logs to identify this cleaner instance.
        - log_enabled: If True, log messages will be printed to stdout.
        """
        self.df = df  # Direct use, no .copy()
        self.name = name
        self.log_enabled = log_enabled

    def _log(self, message: str):
        """
        Internal helper to print log messages only when logging is enabled.
        """
        if self.log_enabled:
            print(message)

    def drop_columns(self, columns: list):
        """
        Drop specified columns from the DataFrame if they exist.

        Parameters:
        - columns: List of column names to drop.
        """
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
        """
        Apply data type conversions to columns as specified in the mapping.

        Parameters:
        - mapping: Dictionary where keys are column names and values are target data types.
                   Supported types: 'datetime', 'numeric', 'str', 'bool', or any valid numpy/pandas dtype.
        """
        self._log(f"\n=== {self.name} — Applying Type Mappings ===")
        if mapping is None:
            self._log("No mapping provided.")
            return

        converted = []
        failed = []
        skipped = []

        # Only keep columns that exist in the DataFrame
        valid_mapping = {col: typ for col, typ in mapping.items() if col in self.df.columns}
        skipped = [col for col in mapping if col not in self.df.columns]

        # Convert all datetime columns in bulk
        datetime_cols = [col for col, typ in valid_mapping.items() if typ == 'datetime']
        if datetime_cols:
            try:
                self.df[datetime_cols] = self.df[datetime_cols].apply(
                    pd.to_datetime, errors='coerce', utc=True
                )
                converted.extend([(col, 'datetime') for col in datetime_cols])
            except Exception:
                failed.extend(datetime_cols)

        # Convert all 'str' and 'bool' columns using bulk astype
        astype_map = {col: typ for col, typ in valid_mapping.items() if typ in ['str', 'bool']}
        if astype_map:
            try:
                self.df = self.df.astype(astype_map)
                converted.extend(astype_map.items())
            except Exception:
                failed.extend(astype_map.keys())

        # Handle other types individually (e.g. 'numeric', custom dtypes)
        for col, typ in valid_mapping.items():
            if typ in ['datetime', 'str', 'bool']:
                continue  # Already handled
            try:
                if typ == 'numeric':
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                else:
                    self.df[col] = self.df[col].astype(typ)
                converted.append((col, typ))
            except Exception:
                failed.append(col)

        # Logging results
        if converted:
            self._log("Converted columns: " + ", ".join(f"{col}: {typ}" for col, typ in converted))
        if skipped:
            self._log(f"Skipped (not in DataFrame): {', '.join(skipped)}")
        if failed:
            self._log(f"Failed to convert: {', '.join(failed)}")

    def rename_columns(self, rename_map: dict):
        """
        Rename columns in the DataFrame using a provided mapping.

        Parameters:
        - rename_map: Dictionary mapping old column names to new names.
        """
        self._log(f"\n=== {self.name} — Renaming Columns ===")
        existing = {k: v for k, v in rename_map.items() if k in self.df.columns}
        missing = [k for k in rename_map if k not in self.df.columns]

        if existing:
            self.df.rename(columns=existing, inplace=True)
            self._log("Renamed columns: " + ", ".join(f"{k} -> {v}" for k, v in existing.items()))
        else:
            self._log("No columns were renamed.")

        if missing:
            self._log(f"Skipped (not found): {', '.join(missing)}")

    def normalize_nones(self):
        """
        Replace string values 'None' and 'null' (as text) with pandas NA (missing values).
        """
        self._log(f"\n=== {self.name} — Replacing 'None'/'null' strings with NaN ===")
        self.df.replace(["None", "null"], pd.NA, inplace=True)

    def get_cleaned_df(self):
        """
        Return the cleaned DataFrame.

        Returns:
        - pandas DataFrame after all applied transformations.
        """
        return self.df
