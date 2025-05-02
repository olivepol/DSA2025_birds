import numpy as np
import pandas as pd

def levenshtein(a, b, ratio=True, lowercase=True):
    if lowercase:
        a = a.lower()
        b = b.lower()
    if not a or not b:
        return 0.0 if ratio else max(len(a), len(b))
    if len(a) > len(b):
        a, b = b, a
    distances = np.zeros((len(a) + 1, len(b) + 1))
    for i in range(len(a) + 1):
        distances[i][0] = i
    for j in range(len(b) + 1):
        distances[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            distances[i][j] = min(
                distances[i - 1][j] + 1,
                distances[i][j - 1] + 1,
                distances[i - 1][j - 1] + cost,
            )
    if ratio:
        return (len(a) + len(b) - distances[len(a)][len(b)]) / (len(a) + len(b))
    return distances[len(a)][len(b)]

def get_top_matches(df, user_input, location=None, top_n=5):
    if location:
        df = df[df['district'].str.lower() == location.lower()]
    df = df.copy()
    df['similarity'] = df['last_name'].apply(lambda x: levenshtein(user_input, str(x), ratio=True))
    return df.sort_values(by='similarity', ascending=False).head(top_n)