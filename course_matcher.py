# course_matcher.py

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
from langdetect import detect
from rapidfuzz import fuzz
from deep_translator import GoogleTranslator

class CourseMatcher:
    def __init__(self, df: pd.DataFrame, model, course_embeddings: Optional[np.ndarray] = None):
        """Initialize the course matcher.
        
        Args:
            df: DataFrame containing course data
            model: Sentence transformer model
            course_embeddings: Pre-computed course embeddings (if available)
        """
        self.df = df
        self.model = model
        self.course_embeddings = course_embeddings
    
    def translate_query_to_german(self, query: str) -> str:
        """Translate a query to German if it's not already in German."""
        try:
            return GoogleTranslator(source='auto', target='de').translate(query)
        except Exception as e:
            raise ValueError(f"Translation failed: {e}")
    
    def get_course_matches(self, user_query: str, user_budget: float, top_n: int = 20, 
                          similarity_threshold: float = 0.45) -> pd.DataFrame:
        """Find courses matching the user query within budget constraints."""
        # Implement the get_course_matches function from your notebook
        # Include query translation, fuzzy matching, semantic search, and price filtering
        
    def run(self, user_query: str, user_budget: float) -> pd.DataFrame:
        """Main method to run the course matching pipeline."""
        try:
            return self.get_course_matches(user_query, user_budget)
        except Exception as e:
            # Handle exceptions appropriately
            raise