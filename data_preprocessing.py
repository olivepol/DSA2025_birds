# data_preprocessing.py

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class DataPreprocessor:
    def __init__(self, json_path: str, excel_path: str, translation_map_path: Optional[str] = None):
        """Initialize with paths to data sources and translation map if available."""
        self.json_path = json_path
        self.excel_path = excel_path
        self.translation_map_path = translation_map_path
        self.translation_map = None
        self.df_merged = None
        
    def load_json_data(self) -> pd.DataFrame:
        """Load course data from JSON file."""
        # Return DataFrame with German course data
        
    def load_excel_data(self) -> pd.DataFrame:
        """Load translated data from Excel file."""

        # Return DataFrame with English course data
        
    def load_translation_map(self) -> Dict:
        """Load saved translation map from JSON file."""
        
    def get_column_translation_mapping(self) -> Dict:
        """Return the German to English column name mapping."""
        # Define and return column translation dictionary
        
    def merge_dataframes(self, df_german, df_eng) -> pd.DataFrame:
        """Merge German and English dataframes."""
        # Implementation based on your notebook code
        
    def apply_transformations(self) -> pd.DataFrame:
        """Apply all transformations to the merged dataframe."""
        # Convert numeric columns
        # Calculate occupancy metrics
        # Create gender distribution features
        # One-hot encode target groups
        
    def preprocess_data(self) -> pd.DataFrame:
        """Main method to run the entire preprocessing pipeline."""
        df_german = self.load_json_data()
        df_eng = self.load_excel_data()
        
        # Merge the dataframes
        self.df_merged = self.merge_dataframes(df_german, df_eng)
        
        # Load translation map if available
        if self.translation_map_path:
            self.translation_map = self.load_translation_map()
            self.df_merged['course_name_translated'] = self.df_merged['course_name_german'].map(self.translation_map)
        
        # Apply all transformations
        self.df_merged = self.apply_transformations()
        
        return self.df_merged