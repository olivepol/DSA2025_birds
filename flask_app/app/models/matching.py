# matching.py
import pandas as pd
import numpy as np
import json
from langdetect import detect
from deep_translator import GoogleTranslator
from rapidfuzz import fuzz


def translate_query_to_german(query):
    try:
        return GoogleTranslator(source='auto', target='de').translate(query)
    except Exception as e:
        raise ValueError(f"Translation failed: {e}")


def get_course_matches(user_query, df, user_budget, top_n=20, similarity_threshold=0.45):
    if not isinstance(user_query, str) or not user_query.strip():
        raise ValueError("Invalid input. Please provide a non-empty search query.")

    try:
        detected_lang = detect(user_query)
    except Exception:
        detected_lang = "en"

    translated_query = user_query if detected_lang == 'de' else translate_query_to_german(user_query)
    search_tokens = translated_query.lower().split()
    use_partial = len(search_tokens) > 1

    def fuzzy_token_match(text):
        if pd.isna(text): return False
        if isinstance(text, list):
            text = " ".join(text)
        text = text.lower()
        if use_partial:
            return any(fuzz.partial_ratio(token, text) >= 75 for token in search_tokens)
        else:
            return any(fuzz.token_set_ratio(token, text) >= 60 for token in search_tokens)


    df_filtered = df[
        df['course_name_german'].apply(fuzzy_token_match) |
        df['course_name_translated'].apply(fuzzy_token_match)|
        df['search_text'].apply(fuzzy_token_match)
    ]

    if df_filtered.empty:
        raise ValueError("No courses matched for search input. Try a different query.")

    # Compute fuzzy match score as a proxy for semantic score
    df_filtered = df_filtered.copy()
    df_filtered['semantic_score'] = df_filtered['course_name_german'].apply(
    lambda name: fuzz.token_set_ratio(translated_query.lower(), name.lower()) / 100 if pd.notna(name) else 0
    )

    if user_budget and user_budget > 0:
        min_price = user_budget * 0.7
        max_price = user_budget * 1.3
        df_filtered = df_filtered[df_filtered['price_amount'].between(min_price, max_price)]

        if df_filtered.empty:
            raise ValueError("No matches for this price filter, please remove filter to see all matches.")

        def compute_penalty(price):
            if price >= user_budget:
                penalty = (price- user_budget) / (0.3 * user_budget)  
            else:
                penalty = (user_budget- price) / (0.3 * user_budget)
            return max(0, min(1, penalty))

        df_filtered['price_penalty_scaled'] = df_filtered['price_amount'].apply(compute_penalty)
    
        df_filtered['final_score'] = (
            0.65 * df_filtered['semantic_score'] +
            0.35 * (1 - df_filtered['price_penalty_scaled'])
        )
    else:
        df_filtered['final_score'] = df_filtered['semantic_score']

    top_courses = df_filtered.sort_values(by='final_score', ascending=False).head(top_n).copy()
    top_courses['final_rank'] = np.arange(1, len(top_courses) + 1)

    return top_courses
