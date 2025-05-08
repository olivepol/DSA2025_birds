from app.models.matching import CourseMatcher
from app.models.platform_ranker import PlatformPreferenceRanker
from app.models.consensus_ranker import ConsensusRanker

def process_user_inputs(user_query, user_budget, user_gender, user_target_groups, df):
    """
    Full processing pipeline to produce a consensus-ranked list of course matches.

    Args:
        user_query (str): User's search query.
        user_budget (float): Budget filter to narrow results.
        user_gender (str): Gender string for demographic targeting.
        user_target_groups (list): List of groups the user identifies with.
        df (pd.DataFrame): Course catalog DataFrame.

    Returns:
        pd.DataFrame: Final ranked course list.
    """
    # Step 1: Match courses based on match score and price-based filters
    matcher = CourseMatcher(df=df, user_query=user_query, user_budget=user_budget)
    final_matches_df = matcher.run()

    # Step 2: Rank based on platform preference (e.g., inclusivity, target groups, sponsorship)
    ranker = PlatformPreferenceRanker(user_gender=user_gender, selected_target_groups=user_target_groups)
    platform_ranked_df = ranker.rank(final_matches_df)

    # Step 3: Consensus ranking to reconcile user and platform preferences
    consensus = ConsensusRanker(final_matches_df, platform_ranked_df)
    final_output_df = consensus.get_ranked_df()

    return final_output_df
