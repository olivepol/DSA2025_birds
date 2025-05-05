# preference_ranker.py

import pandas as pd
from typing import List, Dict, Optional

class PlatformPreferenceRanker:
    # Define the target group mapping as a class variable
    TARGET_GROUP_MAPPING = {
        "People with a migration background": "Menschen mit Migrationshintergrund",
        "Illiterate people": "Analphabet/inn/en",
        "Women": "Frauen",
        "People with disabilities": "Menschen mit Behinderung",
        "Older adults / older people": "Ältere",
        "Other target groups": "Andere Adressaten-gruppen",
        "Children": "Kinder",
        "Adolescents / young people": "Jugendliche"
    }
    
    def __init__(self, user_gender: str, selected_target_groups: List[str]):
        """Initialize the ranker with user preferences.
        
        Args:
            user_gender: 'male' or 'female'
            selected_target_groups: List of target groups the user belongs to
        """
        # Implementation from your notebook
        
    def rank(self, matched_df: pd.DataFrame) -> pd.DataFrame:
        """Rank the matched courses based on platform preferences."""
        # Implementation from your notebook
        # Return the ranked DataFrame