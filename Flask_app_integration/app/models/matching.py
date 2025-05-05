# matching.py
import pandas as pd
import numpy as np
import json
from langdetect import detect
from deep_translator import GoogleTranslator
from rapidfuzz import fuzz
from sklearn.metrics.pairwise import cosine_similarity

def translate_query_to_german(query):
    try:
        return GoogleTranslator(source='auto', target='de').translate(query)
    except Exception as e:
        raise ValueError(f"Translation failed: {e}")

def get_course_matches(user_query, df, model, course_embeddings, user_budget, top_n=20, similarity_threshold=0.45):
    if not isinstance(user_query, str) or not user_query.strip():
        raise ValueError("Invalid input. Please provide a non-empty search query.")

    try:
        detected_lang = detect(user_query)
    except Exception:
        detected_lang = "en"

    translated_query = user_query if detected_lang == 'de' else translate_query_to_german(user_query)
    search_tokens = translated_query.lower().split()

    def fuzzy_token_match(text):
        if pd.isna(text): return False
        text = text.lower()
        return any(fuzz.partial_ratio(token, text) >= 50 for token in search_tokens)

    df_filtered = df[
        df['course_name_german'].apply(fuzzy_token_match) |
        df['course_name_translated'].apply(fuzzy_token_match)
    ]

    if df_filtered.empty:
        raise ValueError("No courses matched any extracted keyword tokens. Try a different query.")

    query_embedding = model.encode([translated_query])
    filtered_embeddings = model.encode(df_filtered['search_text'].tolist())
    similarities = cosine_similarity(query_embedding, filtered_embeddings)[0]

    df_filtered = df_filtered.copy()
    df_filtered['semantic_score'] = similarities
    df_filtered = df_filtered[similarities >= similarity_threshold]

    if df_filtered.empty:
        raise ValueError("Courses matched the keywords, but were semantically too distant.")

    if user_budget and user_budget > 0:
        min_price = user_budget * 0.7
        max_price = user_budget * 1.3
        df_filtered = df_filtered[df_filtered['price_amount'].between(min_price, max_price)]

        if df_filtered.empty:
            raise ValueError("No matches for this price filter, please remove filter to see all matches.")

        def compute_penalty(price):
            if price >= user_budget:
                penalty = (1.3 * user_budget - price) / (0.3 * user_budget)
            else:
                penalty = (price - 0.7 * user_budget) / (0.3 * user_budget)
            return max(0, min(1, penalty))

        df_filtered['price_penalty_scaled'] = df_filtered['price_amount'].apply(compute_penalty)
        avg_sem_score = df_filtered['semantic_score'].nlargest(top_n).mean()
        df_filtered['weighted_price_penalty'] = df_filtered['price_penalty_scaled'] * avg_sem_score

        df_filtered['final_score'] = (
            0.65 * df_filtered['semantic_score'] +
            0.35 * (1 - df_filtered['weighted_price_penalty'])
        )
    else:
        # Skip price filtering and penalty, use semantic score directly
        df_filtered['final_score'] = df_filtered['semantic_score']

    top_courses = df_filtered.sort_values(by='final_score', ascending=False).head(top_n).copy()
    top_courses['final_rank'] = np.arange(1, len(top_courses) + 1)

    return top_courses
