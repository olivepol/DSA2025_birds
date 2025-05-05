import os
import pandas as pd

class AssetLoader:
    def __init__(self, df_path):
        print("\U0001F4E6 [AssetLoader] Initializing...")
        print(f"\U0001F4C1 df_path: {df_path} — exists: {os.path.exists(df_path)}")

        if not os.path.exists(df_path):
            raise FileNotFoundError(f"DataFrame path not found: {df_path}")

        self.df = pd.read_pickle(df_path)

    def get_dataframe(self):
        return self.df.copy()