import pandas as pd
import numpy as np

class EDAService:
    def __init__(self, df: pd.DataFrame, name: str = "DataFrame", preview_rows: int = 5):
        self.df = df
        self.name = name
        self.preview_rows = preview_rows

    def run_step(self, step: int):
        # Logical order of steps for effective EDA
        if step == 1:
            self.structure_overview()  # Shape and types
        elif step == 2:
            self.sample_preview()  # First few rows
        elif step == 3:
            self.missing_values()  # Absolute missing counts
        elif step == 4:
            self.null_percentage()  # Percentage missing
        elif step == 5:
            self.duplicate_rows(show_samples=False)
        elif step == 6:
            self.numeric_summary()
        elif step == 7:
            self.value_ranges()
        elif step == 8:
            self.categorical_summary(top_n=5)
        elif step == 9:
            self.correlation_matrix()
        else:
            print(f"Invalid step: {step}")

    def structure_overview(self, max_cols: int = 50):
        # Purpose: Understand shape, types, and representative values clearly
        print(f"\n=== {self.name} — Structure Overview ===")
        row_count, col_count = self.df.shape
        print(f"Rows: {row_count}")
        print(f"Columns: {col_count}\n")

        print("Column counts by type:")
        type_counts = self.df.dtypes.value_counts()
        for dtype, count in type_counts.items():
            percentage = (count / col_count) * 100
            print(f"- {dtype}: {count} columns ({percentage:.1f}%)")

        print("\nExample column names by type:")
        grouped = self.df.dtypes.groupby(self.df.dtypes)
        for dtype, cols in grouped.groups.items():
            cols_list = list(cols)
            shown_cols = cols_list[:max_cols]
            print(f"\n{dtype} ({len(cols_list)} columns):")
            print(", ".join(str(c) for c in shown_cols) + (f" ... (+{len(cols_list) - max_cols} more)" if len(cols_list) > max_cols else ""))

        print("\nNote:")
        print("- object = likely strings, mixed types, or nested structures (e.g., dict/list)")
        print("- int64 / float64 = numeric values")
        print("- bool = True/False data")
        print("- datetime64 = timestamps or date fields")

        print("\nRepresentative values per column:")
        representative_values = {}
        for col in self.df.columns:
            non_null_series = self.df[col].dropna()
            if not non_null_series.empty:
                val = non_null_series.iloc[0]
            else:
                val = None
            representative_values[col] = val
            print(f"- {col}: {repr(val)}")

        return representative_values



    def sample_preview(self, max_cols: int = 20, show_all_rows: bool = False):
        # Purpose: Get a feel for what the data looks like
        print(f"\n=== {self.name} — Sample Preview ===")
        pd.set_option("display.max_columns", max_cols)
        print(self.df if show_all_rows else self.df.head(self.preview_rows))
        pd.reset_option("display.max_columns")

    def missing_values(self):
        # Purpose: Identify which columns have missing values (absolute)
        print(f"\n=== {self.name} — Missing Values (count) ===")
        missing = self.df.isnull().sum()
        missing = missing[missing > 0]
        if missing.empty:
            print("No missing values.")
        else:
            print(missing.sort_values(ascending=False))

    def null_percentage(self):
        # Purpose: Prioritize columns with the highest proportion of missing data
        print(f"\n=== {self.name} — Missing Values (percentage) ===")
        total = len(self.df)
        nulls = (self.df.isnull().sum() / total * 100).sort_values(ascending=False)
        nulls = nulls[nulls > 0]
        if nulls.empty:
            print("No missing value percentages above zero.")
        else:
            print(nulls.round(2))

    def duplicate_rows(self, show_samples: bool = True):
        # Purpose: Detect and optionally inspect duplicate rows (based on hashable columns)
        print(f"\n=== {self.name} — Duplicate Rows ===")
        hashable_cols = [col for col in self.df.columns if self.df[col].map(type).isin([int, float, str, bool, type(None)]).all()]
        if not hashable_cols:
            print("No hashable columns to detect duplicates.")
            return

        try:
            dupe_mask = self.df[hashable_cols].duplicated()
            dupe_count = dupe_mask.sum()
            print(f"Duplicate count (based on {len(hashable_cols)} hashable columns): {dupe_count}")
            if dupe_count > 0 and show_samples:
                print(self.df[dupe_mask].head())
        except Exception as e:
            print(f"Error during duplicate detection: {e}")

    def numeric_summary(self):
        # Purpose: Get descriptive statistics of numeric columns
        print(f"\n=== {self.name} — Numeric Summary ===")
        numeric_df = self.df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            print("No numeric columns available.")
        else:
            print(numeric_df.describe())

    def value_ranges(self):
        # Purpose: Check min and max values of numeric columns
        print(f"\n=== {self.name} — Value Ranges (numeric) ===")
        num_df = self.df.select_dtypes(include=[np.number])
        for col in num_df.columns:
            print(f"{col}: min={num_df[col].min()}, max={num_df[col].max()}")

    def categorical_summary(self, top_n: int = 5):
        # Purpose: Identify frequent values in categorical columns
        print(f"\n=== {self.name} — Categorical Summary ===")
        cat_cols = self.df.select_dtypes(include=["object", "category"]).columns
        if not len(cat_cols):
            print("No categorical columns found.")
            return
        for col in cat_cols:
            print(f"\nColumn: {col}")
            print(self.df[col].value_counts().head(top_n))

    def correlation_matrix(self):
        # Purpose: Explore relationships between numeric variables
        print(f"\n=== {self.name} — Correlation Matrix ===")
        num_df = self.df.select_dtypes(include=[np.number])
        if num_df.empty:
            print("No numeric columns present.")
        else:
            print(num_df.corr(numeric_only=True))