import itertools
import pandas as pd
import pulp

class ConsensusRanker:
    """
    Class to compute a consensus ranking from two ranked lists (user and platform)
    using a Kemeny-Young voting model solved via integer linear programming.
    """

    def __init__(self, user_df: pd.DataFrame, platform_df: pd.DataFrame):
        """
        Initialize the ranker with user and platform rankings.

        Args:
            user_df (pd.DataFrame): DataFrame with user rankings. Must include 'guid' column.
            platform_df (pd.DataFrame): DataFrame with platform rankings. Must include 'guid' column.

        Raises:
            ValueError: If the GUIDs in user and platform data do not match.
        """
        self.user_df = user_df
        self.platform_df = platform_df
        self.user_order = list(user_df['guid'])
        self.platform_order = list(platform_df['guid'])

        if set(self.user_order) != set(self.platform_order):
            raise ValueError("user_order and platform_order must contain the same GUIDs")

    def compute_consensus(self):
        """
        Compute a consensus ranking based on weighted pairwise preferences.

        Returns:
            list: A list of GUIDs in the consensus order.
        """
        courses = self.user_order
        user_rank = {c: i for i, c in enumerate(self.user_order)}
        platform_rank = {c: i for i, c in enumerate(self.platform_order)}
        w_user, w_plat = 0.5, 0.5  # Equal weight for user and platform input

        # Step 1: Build margin preferences based on both ranks
        margins = {}
        for i, j in itertools.combinations(courses, 2):
            sign_user = 1 if user_rank[i] < user_rank[j] else -1
            sign_plat = 1 if platform_rank[i] < platform_rank[j] else -1
            vote = w_user * sign_user + w_plat * sign_plat

            if vote > 0:
                margins[(i, j)] = abs(vote)
            elif vote < 0:
                margins[(j, i)] = abs(vote)
            else:
                # Tie case: small bidirectional weight to avoid zero
                margins[(i, j)] = 0.1
                margins[(j, i)] = 0.1

        # Step 2: Set up ILP using PuLP
        model = pulp.LpProblem("Kemeny", pulp.LpMinimize)
        x = pulp.LpVariable.dicts('x', (courses, courses), 0, 1, cat='Binary')

        # Objective: Minimize total disagreement with the margins
        model += pulp.lpSum(weight * x[j][i] for (i, j), weight in margins.items())

        # Constraint: one must be ranked higher (antisymmetry)
        for i, j in itertools.permutations(courses, 2):
            model += x[i][j] + x[j][i] == 1

        # Constraint: transitivity
        for i, j, k in itertools.permutations(courses, 3):
            model += x[i][j] + x[j][k] + x[k][i] >= 1

        model.solve(pulp.PULP_CBC_CMD(msg=False))

        # Step 3: Derive order by counting how often each course is ranked above others
        consensus_order = sorted(
            courses,
            key=lambda c: sum(x[c][d].value() for d in courses if d != c),
            reverse=True
        )
        return consensus_order

    def get_ranked_df(self):
        """
        Apply the consensus order to the user_df and return it sorted accordingly.

        Returns:
            pd.DataFrame: Sorted copy of user_df based on consensus rank.
        """
        consensus_order = self.compute_consensus()
        df = self.user_df.copy()
        df['__rank__'] = df['guid'].apply(lambda x: consensus_order.index(x))
        df.sort_values(by='__rank__', inplace=True)
        df.drop(columns='__rank__', inplace=True)
        return df
