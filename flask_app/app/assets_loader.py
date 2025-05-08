import os
import pandas as pd

class AssetLoader:
    """
    Class responsible for loading a serialized pandas DataFrame from app folder.
    Provides a safe interface for accessing the data.
    """

    def __init__(self, df_path):
        """
        Initialize the AssetLoader with the path to a DataFrame file.

        Args:
            df_path (str): Full path to a pickled DataFrame (.pkl).

        Raises:
            FileNotFoundError: If the specified path does not exist.
        """
        print("\U0001F4E6 [AssetLoader] Initializing...")  
        print(f"\U0001F4C1 df_path: {df_path} — exists: {os.path.exists(df_path)}")  

        if not os.path.exists(df_path):
            raise FileNotFoundError(f"DataFrame path not found: {df_path}")

        # Load the DataFrame from the given path
        self.df = pd.read_pickle(df_path)

    def get_dataframe(self):
        """
        Return a copy of the loaded DataFrame to ensure immutability outside the loader.

        Returns:
            pd.DataFrame: A defensive copy of the loaded DataFrame.
        """
        return self.df.copy()
