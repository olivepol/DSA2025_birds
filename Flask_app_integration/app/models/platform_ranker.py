# platform_ranker.py
import pandas as pd

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
    def __init__(self, user_gender: str, selected_target_groups: list):
        self.user_gender = user_gender.lower()
        self.gender_col = 'gap_to_80_percent_women' if self.user_gender == 'female' else 'gap_to_80_percent_men'

        if not self.user_gender or selected_target_groups is None:
            raise ValueError("Please fill in gender field before proceeding.")

        self.selected_target_groups = selected_target_groups.copy()
        if self.user_gender == 'female' and "Women" not in self.selected_target_groups:
            self.selected_target_groups.append("Women")

    def rank(self, matched_df: pd.DataFrame):
        df = matched_df.copy()

        core_cols = ['prop_occupancy_left', 'prop_minimum_to_reach', self.gender_col]
        df['numeric_score'] = df[core_cols].sum(axis=1)
        df = df.sort_values(by='numeric_score', ascending=False).reset_index(drop=True)
        df['rank_index'] = df.index

        binary_cols = ['sponsored']
        for tg in self.selected_target_groups:
            german = TARGET_GROUP_MAPPING.get(tg)
            if german:
                col = f"target_group_{german}"
                if col in df.columns:
                    binary_cols.append(col)
                else:
                    df[col] = 0
                    binary_cols.append(col)

        df['binary_sum'] = df[binary_cols].sum(axis=1)

        max_score = df['numeric_score'].max()
        min_score = df['numeric_score'].min()
        total = len(df)

        def calculate_weight(row):
            if row['rank_index'] > 0:
                return ((max_score - row['numeric_score']) / row['rank_index']) * 1.05
            return ((max_score - min_score) / total) * 1.05

        df['weight'] = df.apply(calculate_weight, axis=1)
        df['binary_boost'] = df['weight'] * df['binary_sum']
        df['final_score_platform'] = df['numeric_score'] + df['binary_boost']
        df = df.sort_values(by='final_score_platform', ascending=False).reset_index(drop=True)

        return df