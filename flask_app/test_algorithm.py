import unittest
import numpy as np
import pandas as pd
from copy import deepcopy

# Load preprocessed course data
df_merged = pd.read_pickle("app/Processed_data_for_app.pkl")

# Import from your app structure
from app.models.matching import get_course_matches
from app.models.platform_ranker import PlatformPreferenceRanker
from app.models.consensus_ranker import ConsensusRanker

class TestCourseMatchingPipeline(unittest.TestCase):

    def test_unit_1_course_matcher(self):
        result = get_course_matches(
            user_query="English for beginners",
            df=df_merged,
            user_budget=100
        )
        self.assertFalse(result.empty, "No matches returned")
        self.assertTrue((result['price_amount'] <= 130).all(), "Some prices exceed 130% budget")
        self.assertIn('match_score', result.columns)
        self.assertIn('final_score', result.columns)
        print("Unit Test 1 passed")

    def test_unit_2_1_platform_flex_boost(self):
        test_df = deepcopy(df_merged.head(10))
        test_df = test_df[test_df['price_amount'].notna()]
        test_df = test_df[test_df['prop_occupancy_left'] > 0]
        target_col = "target_group_Frauen"
        if target_col not in test_df.columns:
            test_df[target_col] = 0
        test_df.loc[test_df.index[0], target_col] = 1

        ranker = PlatformPreferenceRanker(user_gender="female", selected_target_groups=["Women"])
        ranked = ranker.rank(test_df)

        self.assertTrue((ranked[target_col] == 1).any(), "No women-targeted courses found")
        self.assertTrue((ranked.head(5)[target_col] == 1).any(), "No women-targeted course in top 5")
        print("Unit Test 2.1 passed")

    def test_unit_3_consensus_differs_from_inputs(self):
        user_df = get_course_matches("English for beginners", df_merged, user_budget=100)
        ranker = PlatformPreferenceRanker("female", ["Women"])
        platform_df = ranker.rank(user_df)

        consensus = ConsensusRanker(user_df=user_df, platform_df=platform_df)
        consensus_df = consensus.get_ranked_df()

        self.assertFalse(consensus_df.empty)
        self.assertNotEqual(list(consensus_df['guid']), list(user_df['guid']), "Consensus = user rank")
        self.assertNotEqual(list(consensus_df['guid']), list(platform_df['guid']), "Consensus = platform rank")
        print("Unit Test 3 passed")

    def test_integration_matcher_pipeline(self):
        result = get_course_matches("Computer basics", df_merged, user_budget=80)
        self.assertFalse(result.empty)
        self.assertIn('match_score', result.columns)
        self.assertIn('final_score', result.columns)
        self.assertLessEqual(result['final_score'].max(), 1.0)
        print("Integration Test passed")

    def test_end_to_end_pipeline(self):
        matches = get_course_matches("German A1", df_merged, user_budget=100)
        ranker = PlatformPreferenceRanker("female", ["Women"])
        platform_df = ranker.rank(matches)
        consensus = ConsensusRanker(matches, platform_df)
        final_df = consensus.get_ranked_df()

        self.assertFalse(final_df.empty)
        self.assertIn('course_name_german', final_df.columns)
        print("End-to-End Test passed")

if __name__ == '__main__':
    unittest.main(verbosity=2)