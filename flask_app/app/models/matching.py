import pandas as pd
import numpy as np
from langdetect import detect
from deep_translator import GoogleTranslator
from rapidfuzz import fuzz

class CourseMatcher:
    """
    A class to match courses based on user query using fuzzy logic. 
    Then filter and rank results by looking at user budget.
    Handles language detection, translation, and scoring based on string match similarity and price deviation.
    """

    def __init__(self, df, user_query, user_budget=None, top_n=20):
        """
        Initialize the matcher with course data, user query, and optional budget.

        Args:
            df (pd.DataFrame): The course dataset containing required columns.
            user_query (str): The user's search query (can be in English or German).
            user_budget (float, optional): User's price budget. Defaults to None.
            top_n (int, optional): Number of top results to return. Defaults to 20.
        """
        self.df = df
        self.user_query = user_query
        self.user_budget = user_budget
        self.top_n = top_n
        self.translated_query = None
        self.search_tokens = []
        self.use_partial = False
        self.filtered_df = None

    def preprocess_query(self):
        """
        Detect language and translate query to German if needed.
        Tokenize and determine matching strategy.
        """
        if not isinstance(self.user_query, str) or not self.user_query.strip():
            raise ValueError("Invalid input. Please provide a non-empty search query.")

        try:
            detected_lang = detect(self.user_query)
        except Exception:
            detected_lang = "en"

        # Translate to German if the detected language is not German
        if detected_lang != 'de':
            try:
                self.translated_query = GoogleTranslator(source='auto', target='de').translate(self.user_query)
            except Exception as e:
                raise ValueError(f"Translation failed: {e}")
        else:
            self.translated_query = self.user_query

        self.search_tokens = self.translated_query.lower().split()
        self.use_partial = len(self.search_tokens) > 1

    def fuzzy_token_match(self, text, partial_threshold=75, token_set_threshold=60):
        """
        Apply fuzzy token matching to a given text field.
        Use partial matching for multi-word queries and token set ratio for single-word queries.

        Args:
            text (str or list): Text to match against search tokens.
            partial_threshold (int): Minimum fuzz.partial_ratio score (0–100) for multi-word tokens.
            token_set_threshold (int): Minimum fuzz.token_set_ratio score (0–100) for single-word tokens.

        Returns:
            bool: True if the text matches any token with sufficient fuzziness, False otherwise.
        """
        if pd.isna(text):
            return False
        if isinstance(text, list):
            text = " ".join(text)
        text = text.lower()

        if self.use_partial:
            return any(fuzz.partial_ratio(token, text) >= partial_threshold for token in self.search_tokens)
        else:
            return any(fuzz.token_set_ratio(token, text) >= token_set_threshold for token in self.search_tokens)
        

    def match_courses(self):
        """
        Filter DataFrame using fuzzy matching across relevant text columns.

        Raises:
            ValueError: If no matching courses are found.
        """
        self.filtered_df = self.df[
            self.df['course_name_german'].apply(self.fuzzy_token_match) |
            self.df['course_name_translated'].apply(self.fuzzy_token_match) |
            self.df['search_text'].apply(self.fuzzy_token_match)
        ]

        if self.filtered_df.empty:
            raise ValueError("No courses matched for search input. Try a different query.")

    def compute_scores(self):
        """
        Compute fuzzy match score and apply budget filter and scoring logic if applicable.

        Raises:
            ValueError: If budget filter removes all matches.
        """
        self.filtered_df = self.filtered_df.copy()

        # Compute match score based on query vs. German course name and scale it to [0, 1]
        self.filtered_df['match_score'] = self.filtered_df['course_name_german'].apply(
            lambda name: fuzz.token_set_ratio(self.translated_query.lower(), name.lower()) / 100 if pd.notna(name) else 0
        )

        #filter out courses that are not within 30% of the user's budget

        if self.user_budget and self.user_budget > 0:
            min_price = self.user_budget * 0.7
            max_price = self.user_budget * 1.3

            self.filtered_df = self.filtered_df[self.filtered_df['price_amount'].between(min_price, max_price)]

            if self.filtered_df.empty:
                raise ValueError("No matches for this price filter, please remove filter to see all matches.")

            def compute_penalty(price):
                """
                Calculate penalty for price deviation based on user's budget.
                """
                if price >= self.user_budget:
                    penalty = (price - self.user_budget) / (0.3 * self.user_budget)
                else:
                    penalty = (self.user_budget - price) / (0.3 * self.user_budget)
                return max(0, min(1, penalty))

            self.filtered_df['price_penalty'] = self.filtered_df['price_amount'].apply(compute_penalty)

            # Combine match score and price penalty into a final score
            self.filtered_df['final_score'] = (
                0.65 * self.filtered_df['match_score'] +
                0.35 * (1 - self.filtered_df['price_penalty'])
            )
        else:
            # Use match score only when no budget is provided
            self.filtered_df['final_score'] = self.filtered_df['match_score']

    def rank_results(self):
        """
        Rank top results by final score and assign a final rank.

        Returns:
            pd.DataFrame: Top N ranked results.
        """
        top_courses = self.filtered_df.sort_values(by='final_score', ascending=False).head(self.top_n).copy()
        top_courses['final_rank'] = np.arange(1, len(top_courses) + 1)
        return top_courses

    def run(self):
        """
        Execute the full pipeline: preprocess query, match courses, compute scores, and rank.

        Returns:
            pd.DataFrame: Final ranked list of matched courses.
        """
        self.preprocess_query()
        self.match_courses()
        self.compute_scores()
        return self.rank_results()
