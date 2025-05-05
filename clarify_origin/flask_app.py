from flask import Flask, request, redirect, url_for
import pandas as pd
import numpy as np

app = Flask(__name__)

# --- load course data from CSV ---
df_courses = pd.read_csv("subset_20percent_translated_final.csv")
df_courses['category_label'] = df_courses['last_name'].fillna('') + ' ' + df_courses['subtitle'].fillna('')

# --- matching algorithm ---
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
    df['similarity'] = df['category_label'].apply(
        lambda x: levenshtein(user_input, str(x), ratio=True)
    )
    return df.sort_values(by='similarity', ascending=False).head(top_n)

# --- routes ---
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        query = request.form['query']
        location = request.form['location']
        return redirect(url_for('match_test', query=query, location=location))

    return '''
        <h1>Welcome to the Course Matcher!</h1>
        <form method="post">
            <label for="query">Search query:</label><br>
            <input type="text" id="query" name="query" placeholder="e.g. introduction" required><br><br>

            <label for="location">District (optional):</label><br>
            <input type="text" id="location" name="location" placeholder="e.g. Mitte"><br><br>

            <input type="submit" value="Find Matches">
        </form>
        <p>Try "introduction" and "Mitte" to see results.</p>
    '''

@app.route('/match')
def match_test():
    query = request.args.get('query', '')
    location = request.args.get('location', '')
    matches = get_top_matches(df_courses, query, location)
    html = f"<h2>Top Matches for '{query}' in '{location}'</h2><ul>"
    for _, row in matches.iterrows():
        html += f"<li>{row['category_label']} ({row['district']}) - Similarity: {row['similarity']:.2f}</li>"
    html += "</ul><a href='/'>Back</a>"
    return html

if __name__ == '__main__':
    app.run(debug=True)