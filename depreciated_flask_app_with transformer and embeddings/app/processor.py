# processor.py
from app.models.matching import get_course_matches
from app.models.platform_ranker import PlatformPreferenceRanker
from app.models.consensus_ranker import ConsensusRanker

class CourseMatcher:
    def __init__(self, df, model, course_embeddings):
        self.df = df
        self.model = model
        self.embeddings = course_embeddings

    def run(self, user_query, user_budget):
        return get_course_matches(
            user_query=user_query,
            df=self.df,
            model=self.model,
            course_embeddings=self.embeddings,
            user_budget=user_budget
        )

def process_user_inputs(user_query, user_budget, user_gender, user_target_groups, model, df, course_embeddings):
    matcher = CourseMatcher(df=df, model=model, course_embeddings=course_embeddings)
    final_matches_df = matcher.run(user_query=user_query, user_budget=user_budget)

    ranker = PlatformPreferenceRanker(user_gender=user_gender, selected_target_groups=user_target_groups)
    platform_ranked_df = ranker.rank(final_matches_df)

    consensus = ConsensusRanker(final_matches_df, platform_ranked_df)
    final_output_df = consensus.get_ranked_df()

    return final_output_df
