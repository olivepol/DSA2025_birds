import unittest
import numpy as np
import pandas as pd
from copy import deepcopy

# these need to be already defined/imported in the test context:
# - CourseMatcher
# - PlatformPreferenceRanker
# - ConsensusRanker
# - get_course_matches
# - df_merged
# - model
# - course_embeddings

class TestCourseMatchingPipeline(unittest.TestCase):

    def test_unit_1_course_matcher(self):
        matcher = CourseMatcher(df=df_merged, model=model, course_embeddings=course_embeddings)
        result = matcher.run(user_query="English for beginners", user_budget=100)

        self.assertFalse(result.empty, "No matches returned")
        self.assertTrue((result['price_amount'] <= 130).all(), "Some prices exceed 130% budget")
        self.assertIn('semantic_score', result.columns)
        self.assertIn('final_score', result.columns)
        print("Unit Test 1 passed")

    def test_unit_2_1_platform_flex_boost(self):
        # create test copy and inject a women-aligned course
        test_df = deepcopy(final_matches_df)
        target_col = "target_group_Frauen"
        test_df[target_col] = 0
        test_df.loc[test_df.index[0], target_col] = 1

        print("Before ranking:", test_df[target_col].value_counts())

        ranker = PlatformPreferenceRanker(user_gender="female", selected_target_groups=["Women"])
        ranked = ranker.rank(test_df)

        print("After ranking:", ranked[target_col].value_counts())

        self.assertTrue((ranked[target_col] == 1).any(), "No women-targeted courses found in result")
        self.assertTrue((ranked.head(5)[target_col] == 1).any(), "No women-targeted course among top 5")
        print("Unit Test 2.1 passed")

    def test_unit_3_consensus_differs_from_inputs(self):
        matcher = CourseMatcher(df=df_merged, model=model, course_embeddings=course_embeddings)
        user_df = matcher.run(user_query="English for beginners", user_budget=100)

        ranker = PlatformPreferenceRanker(user_gender="female", selected_target_groups=["Women"])
        platform_df = ranker.rank(user_df)

        consensus = ConsensusRanker(user_df=user_df, platform_df=platform_df)
        ranked = consensus.get_ranked_df()

        self.assertFalse(ranked.empty)
        self.assertNotEqual(list(ranked['guid']), list(user_df['guid']), "Consensus matches user order")
        self.assertNotEqual(list(ranked['guid']), list(platform_df['guid']), "Consensus matches platform order")
        print("Unit Test 3 passed")

    def test_integration_matcher_pipeline(self):
        matcher = CourseMatcher(df=df_merged, model=model, course_embeddings=course_embeddings)
        courses = matcher.run(user_query="Computer basics", user_budget=80)

        self.assertFalse(courses.empty)
        self.assertIn('semantic_score', courses.columns)
        self.assertIn('final_score', courses.columns)
        self.assertLessEqual(courses['final_score'].max(), 1.0)
        print("Integration Test passed")

    def test_end_to_end_pipeline(self):
        matcher = CourseMatcher(df=df_merged, model=model, course_embeddings=course_embeddings)
        matches = matcher.run(user_query="German A1", user_budget=100)

        ranker = PlatformPreferenceRanker(user_gender="female", selected_target_groups=["Women"])
        platform_df = ranker.rank(matches)

        consensus = ConsensusRanker(user_df=matches, platform_df=platform_df)
        final_df = consensus.get_ranked_df()

        self.assertFalse(final_df.empty)
        self.assertIn('course_name_german', final_df.columns)
        print("End-to-End Test passed")


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)