import pandas as pd

# Mapping from English user-facing group names to corresponding German column names in data
TARGET_GROUP_MAPPING = {
    "People with a migration background": "Menschen mit Migrationshintergrund",
    "Illiterate people": "Analphabet/inn/en",
    "Women": "Frauen",
    "People with disabilities": "Menschen mit Behinderung",
    "Older adults / older people": "Ältere",
    "Other target groups": "Andere Adressaten–gruppen",
    "Children": "Kinder",
    "Adolescents / young people": "Jugendliche"
}

class PlatformPreferenceRanker:
    """
    Class to rank the final courses that matched the user's search and budget
    based on occupancy available, gender composition, sponsorship status of courses 
    and selected target groups the courses are looking to serve
    Scoring is based inittally on numeric indicators and boosted by binary matches such as sponsorship and target groups.
    """

    def __init__(self, user_gender: str, selected_target_groups: list):
        """
        Initialize the ranker with user gender and selected target groups.

        Args:
            user_gender (str): Gender of the user ("female", "male", etc.), used to select the gender gap column.
            selected_target_groups (list): List of user-identified English group labels.

        Raises:
            ValueError: If gender or selected target groups are missing.
        """
        self.user_gender = user_gender.lower()
        self.gender_col = 'gap_to_80_percent_women' if self.user_gender == 'female' else 'gap_to_80_percent_men'

        if not self.user_gender or not selected_target_groups:
            raise ValueError("Please fill in fields for gender and groups you identify with before proceeding.")

        self.selected_target_groups = selected_target_groups.copy()

        # If the user is female, ensure "Women" is considered in the target groups
        if self.user_gender == 'female' and "Women" not in self.selected_target_groups:
            self.selected_target_groups.append("Women")

        # Attributes used internally during ranking
        self.max_score = None
        self.min_score = None
        self.total = None

    def rank(self, matched_df: pd.DataFrame):
        """
        Rank the matched courses based on numeric and binary indicators.

        Args:
            matched_df (pd.DataFrame): DataFrame containing course/platform rows with required columns:
                - 'prop_occupancy_left', 'prop_minimum_to_reach', gender gap column (based on gender)
                - 'sponsored'
                - one or more 'target_group_<German>' binary columns

        Returns:
            pd.DataFrame: Ranked DataFrame with a final boosted score and sorted by descending preference.
        """
        df = matched_df.copy()

        # Step 1: Compute numeric score (core suitability indicators + gender preference gap)
        core_cols = ['prop_occupancy_left', 'prop_minimum_to_reach', self.gender_col]
        df['numeric_score'] = df[core_cols].sum(axis=1)

        # Step 2: Rank based on numeric score
        df = df.sort_values(by='numeric_score', ascending=False).reset_index(drop=True)
        df['rank_index'] = df.index

        # Step 3: Determine binary boosting columns
        # Includes 'sponsored' and all user-matching target groups
        binary_cols = ['sponsored']  # Sponsorship is always part of boosting
        for tg in self.selected_target_groups:
            german = TARGET_GROUP_MAPPING.get(tg)
            if german:
                col = f"target_group_{german}"
                if col not in df.columns:
                    df[col] = 0  # Assume 0 if column doesn't exist
                binary_cols.append(col)

        # Step 4: Count how many binary criteria each course matches (sponsorship + target groups)
        df['binary_sum'] = df[binary_cols].sum(axis=1)

        # Step 5: Prepare scoring context for weight calculation
        self.max_score = df['numeric_score'].max()
        self.min_score = df['numeric_score'].min()
        self.total = len(df)

        # Step 6: Apply boosting weight and compute final score
        df['weight'] = df.apply(self._calculate_weight, axis=1)
        df['binary_boost'] = df['weight'] * df['binary_sum']
        df['final_score_platform'] = df['numeric_score'] + df['binary_boost']

        # Step 7: Return ranked and sorted results
        return df.sort_values(by='final_score_platform', ascending=False).reset_index(drop=True)

    def _calculate_weight(self, row):
        """
        Internal method to calculate a boosting weight based on the item's rank and how far its numeric score
        is from the maximum. Weight is calculated keeping in mind the average gap between the numeric scores 
        of courses currently ranked, such that boosting ensures ranking modifications where relevant.

        Args:
            row (pd.Series): A row with 'numeric_score' and 'rank_index'.

        Returns:
            float: Weight to apply to the binary match count.
        """
        if row['rank_index'] > 0:
            return ((self.max_score - row['numeric_score']) / row['rank_index']) * 1.05
        else:
            # Use a fair baseline for the top-ranked row to avoid division by zero
            return ((self.max_score - self.min_score) / self.total) * 1.05
