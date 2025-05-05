# main.py

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any

from .data_preprocessing import DataPreprocessor
from .embedding_model import EmbeddingModel
from .course_matcher import CourseMatcher
from .preference_ranker import PlatformPreferenceRanker
from .consensus_ranker import ConsensusRanker

class CourseRecommendationSystem:
    def __init__(self, config: Dict[str, Any]):
        """Initialize the course recommendation system.
        
        Args:
            config: Configuration dictionary with paths and settings
        """
        self.config = config
        self.df_merged = None
        self.model = None
        self.course_embeddings = None
        self._initialize_system()
        
    def _initialize_system(self) -> None:
        """Initialize the system by loading data and models."""
        # Load and preprocess data
        preprocessor = DataPreprocessor(
            json_path=self.config['json_path'],
            excel_path=self.config['excel_path'],
            translation_map_path=self.config.get('translation_map_path')
        )
        self.df_merged = preprocessor.preprocess_data()
        
        # Load embeddings model
        embedding_model = EmbeddingModel(
            model_name=self.config.get('model_name', 'paraphrase-multilingual-MiniLM-L12-v2'),
            model_path=self.config.get('model_path')
        )
        self.model = embedding_model.load_model()
        
        # Load pre-computed embeddings or compute them
        if 'embeddings_path' in self.config and os.path.exists(self.config['embeddings_path']):
            self.course_embeddings = embedding_model.load_embeddings(self.config['embeddings_path'])
        else:
            # Prepare search text
            self.df_merged['search_text'] = (
                self.df_merged['course_name_german'].fillna('') + ' ' + 
                self.df_merged['course_subtitle'].fillna('') + ' ' +
                self.df_merged['keywords_clean'].fillna('')
            )
            
            # Compute embeddings
            self.course_embeddings = embedding_model.encode_texts(self.df_merged['search_text'].tolist())
            
            # Save embeddings if path is provided
            if 'embeddings_path' in self.config:
                embedding_model.save_embeddings(self.course_embeddings, self.config['embeddings_path'])
    
    def recommend_courses(self, user_query: str, user_budget: float, 
                         user_gender: str, user_target_groups: List[str]) -> pd.DataFrame:
        """Recommend courses based on user input.
        
        Args:
            user_query: User's search query
            user_budget: User's budget
            user_gender: User's gender ('male' or 'female')
            user_target_groups: List of target groups the user belongs to
            
        Returns:
            DataFrame with recommended courses
        """
        # Step 1: Match courses based on query and budget
        matcher = CourseMatcher(df=self.df_merged, model=self.model, course_embeddings=self.course_embeddings)
        matched_courses = matcher.run(user_query=user_query, user_budget=user_budget)
        
        # Step 2: Rank according to platform preferences
        ranker = PlatformPreferenceRanker(user_gender=user_gender, selected_target_groups=user_target_groups)
        platform_ranked_courses = ranker.rank(matched_courses)
        
        # Step 3: Compute consensus ranking
        consensus = ConsensusRanker(matched_courses, platform_ranked_courses)
        final_ranked_courses = consensus.get_ranked_df()
        
        return final_ranked_courses