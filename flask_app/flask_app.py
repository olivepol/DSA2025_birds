# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import json
from werkzeug.security import generate_password_hash, check_password_hash
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import ast
from datetime import datetime, timedelta
import itertools, pulp
from flask import abort


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key in production

# Mock user database - replace with a real database in production
users = {}

# --- Helper Functions ---
def safe_parse(x):
    try:
        return ast.literal_eval(x)
    except:
        return x

def extract_first(x, key):
    x = safe_parse(x)
    if isinstance(x, list):
        for entry in x:
            if isinstance(entry, dict) and key in entry:
                return entry[key]
    return None

def extract_description(x):
    x = safe_parse(x)
    if isinstance(x, list):
        for entry in x:
            if isinstance(entry, dict) and entry.get('property') == 'Description':
                return entry.get('text', '')
    return str(x)

def flatten_keywords(x):
    x = safe_parse(x)
    if isinstance(x, list):
        return ', '.join([str(i) for i in x])
    return str(x)

def get_email(x):
    x = safe_parse(x)
    if isinstance(x, dict):
        return x.get('mail')
    return None

def get_contact_fullname(row):
    first = str(row.get('contact_person_first_name', '')).strip()
    last = str(row.get('contact_person_last_name', '')).strip()
    return f"{first} {last}".strip()

def get_address_component(x, component):
    x = safe_parse(x)
    if isinstance(x, list) and len(x) > 0 and isinstance(x[0], dict):
        return x[0].get(component)
    return None

def extract_discount_info(x):
    x = safe_parse(x)
    if isinstance(x, str):
        return x
    return ''


def prepare_course_data(df):
    """Prepare course data for recommendation algorithm"""
    df['description_clean'] = df['description'].apply(extract_description)
    df['keywords_clean'] = df['keywords'].apply(flatten_keywords)

    df['course_weekday'] = df['locations_appointments'].apply(lambda x: extract_first(x, 'weekday'))
    df['course_start_date'] = df['locations_appointments'].apply(lambda x: extract_first(x, 'start_date'))
    df['course_start_time'] = df['locations_appointments'].apply(lambda x: extract_first(x, 'start_time'))
    df['course_end_time'] = df['locations_appointments'].apply(lambda x: extract_first(x, 'end_time'))

    df['registration_email_clean'] = df['registration_email'].apply(get_email)
    df['contact_person_fullname'] = df.apply(get_contact_fullname, axis=1)

    df['address_facility'] = df['locations_address'].apply(lambda x: get_address_component(x, 'facility'))
    df['address_postal_code'] = df['locations_address'].apply(lambda x: get_address_component(x, 'postal_code'))
    df['address_city'] = df['locations_address'].apply(lambda x: get_address_component(x, 'city'))
    df['address_street'] = df['locations_address'].apply(lambda x: get_address_component(x, 'street'))
    df['address_room'] = df['locations_address'].apply(lambda x: get_address_component(x, 'room'))

    # Ensure price is numeric
    df['price_amount'] = pd.to_numeric(df.get('price_amount', np.nan), errors='coerce')

    return df

class SemanticSearchEngine:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.course_embeddings = None
        self.course_texts = None

    def build_index(self, df):
        """Build search index from course data"""
        df['search_text'] = df['course_name'].fillna('') + ' ' + \
                            df['keywords_clean'].fillna('') + ' ' + \
                            df['description_clean'].fillna('')
        self.course_texts = df['search_text'].tolist()
        self.course_embeddings = self.model.encode(self.course_texts, show_progress_bar=True)

    def query(self, user_query, df, top_n=30):
        """Search for courses matching a query"""
        if self.course_embeddings is None:
            raise ValueError("Index not built. Call `build_index(df)` first.")
        query_embedding = self.model.encode([user_query])
        similarities = cosine_similarity(query_embedding, self.course_embeddings)[0]
        top_indices = similarities.argsort()[-top_n:][::-1]
        matched_df = df.iloc[top_indices].copy()
        matched_df['semantic_score'] = similarities[top_indices]
        return matched_df.reset_index(drop=True)
    

class UserPreferenceReranker:
    def __init__(self, weights=None):
        self.weights = weights or {
            'district': 1.0,
            'budget': 0.8,
        }

    def rerank(self, df, prefs):
        """Re-rank courses based on user preferences"""
        # Ensure price is numeric
        df['price_amount'] = pd.to_numeric(df['price_amount'], errors='coerce')
        
        def score(row):
            s = 0
            # Match district
            if str(row.get('district', '')).lower() == prefs.get('district', '').lower():
                s += self.weights['district']
            # Budget logic
            try:
                if pd.notnull(row['price_amount']) and float(row['price_amount']) <= prefs.get('budget_max', float('inf')):
                    s += self.weights['budget']
            except (TypeError, ValueError):
                pass
            return s

        df['match_score'] = df.apply(score, axis=1)
        return df.sort_values(by='match_score', ascending=False).reset_index(drop=True)

def load_course_data():
    """Load and prepare course data from file"""
    try:
        # Try to load the course data from a file
        df = pd.read_excel("sub_20_eng.xlsx", sheet_name="sub_20_eng", header=0)
        df = df.dropna(axis=1, how='all')
        return prepare_course_data(df)
    except Exception as e:
        print(f"Error loading course data: {e}")
        # Fallback to sample data
        return pd.DataFrame([
            {"guid": 1, "course_name": "German A1", "category": "Language", "keywords": "beginner, language, german"},
            {"guid": 2, "course_name": "Yoga for Beginners", "category": "Health", "keywords": "yoga, fitness, beginner"},
            {"guid": 3, "course_name": "Introduction to Python", "category": "Technology", "keywords": "programming, technology, beginner"},
            {"guid": 4, "course_name": "Art History", "category": "Arts", "keywords": "art, history, culture"}
        ])

# Routes
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title="Course Matcher - Volkshochschule Berlin")

@app.route('/interests', methods=['GET', 'POST'])
def interests():
    # Categories of interests for the form
    interest_categories = {
        'Languages': ['German', 'English', 'Spanish', 'French', 'Italian', 'Other languages'],
        'Arts & Crafts': ['Painting', 'Drawing', 'Sculpture', 'Photography', 'Handicrafts'],
        'Health & Fitness': ['Yoga', 'Pilates', 'Meditation', 'Dancing', 'Sports'],
        'Technology': ['Programming', 'Web Development', 'Data Science', 'Digital Marketing'],
        'Other': ['Cooking', 'Music', 'Literature', 'History', 'Philosophy', 'Science']
    }
    
    # Target groups
    target_groups = [
        "People with a migration background",
        "Illiterate people",
        "Women",
        "People with disabilities",
        "Older adults / older people",
        "Other target groups",
        "Children",
        "Adolescents / young people"
    ]
    
    # Weekdays
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Berlin districts
    districts = [
        'Charlottenburg-Wilmersdorf', 'Friedrichshain-Kreuzberg', 'Lichtenberg', 
        'Marzahn-Hellersdorf', 'Mitte', 'Neukölln', 'Pankow', 'Reinickendorf',
        'Spandau', 'Steglitz-Zehlendorf', 'Tempelhof-Schöneberg', 'Treptow-Köpenick'
    ]
    
    return render_template('interests.html', title="Your Interests", 
                           categories=interest_categories, 
                           target_groups=target_groups,
                           weekdays=weekdays,
                           districts=districts)

# Initialize the recommendation engine
semantic_engine = None
courses_df = None


@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    global semantic_engine, courses_df
    
    # Load course data if not already loaded
    if courses_df is None:
        try:
            courses_df = load_course_data()
        except Exception as e:
            flash(f"Error loading course data: {e}")
            return render_template('recommendations.html', title="Error", courses=[], interests=[])
    
    # Initialize semantic search engine if not already initialized
    if semantic_engine is None:
        try:
            semantic_engine = SemanticSearchEngine()
            semantic_engine.build_index(courses_df)
        except Exception as e:
            flash(f"Error initializing search engine: {e}")
            return render_template('recommendations.html', title="Error", courses=[], interests=[])
    
    if request.method == 'POST':
        # Process the submitted interests directly from the form
        selected_interests = request.form.getlist('interests')
        gender = request.form.get('gender', 'not_specified')
        selected_target_groups = request.form.getlist('target_groups')
        district = request.form.get('district', '')
        budget_max = float(request.form.get('budget_max', 100))
        preferred_days = request.form.getlist('preferred_days')
        learning_goal = request.form.get('learning_goal', 'personal')
        availability = request.form.getlist('availability')
        
        # Store preferences in session instead of user profile
        session['preferences'] = {
            'interests': selected_interests,
            'gender': gender,
            'target_groups': selected_target_groups,
            'district': district,
            'budget_max': budget_max,
            'preferred_days': preferred_days,
            'learning_goal': learning_goal,
            'availability': availability
        }
    else:
        # Get preferences from session if they exist
        if 'preferences' not in session:
            flash("Please select your interests first.")
            return redirect(url_for('interests'))
    
    # Get user's interests and preferences from session
    preferences = session.get('preferences', {})
    interests = ', '.join(preferences.get('interests', []))
    
    if not interests:
        flash("Please select at least one interest to get recommendations.")
        return redirect(url_for('interests'))
    
    user_preferences = {
        'district': preferences.get('district', ''),
        'budget_max': preferences.get('budget_max', 100),
        'preferred_days': preferences.get('preferred_days', []),
        'start_after': datetime.now(),
        'end_before': datetime.now() + timedelta(days=365)
    }
    
    # Get user's gender and target groups
    user_gender = preferences.get('gender', 'not_specified')
    selected_target_groups = preferences.get('target_groups', [])
    
    # Execute the recommendation pipeline
    try:
        # Step 1: Semantic search
        sem_matches = semantic_engine.query(interests, courses_df, top_n=25)
        
        # Step 2: User preference reranking
        reranker = UserPreferenceReranker()
        ranked_df = reranker.rerank(sem_matches, user_preferences)
        
        # For now, just return the ranked results without platform ranking
        recommended_courses = ranked_df.head(10).to_dict('records')
        
        return render_template('recommendations.html', title="Your Course Recommendations", 
                              courses=recommended_courses, interests=preferences.get('interests', []))
    except Exception as e:
        flash(f"Error generating recommendations: {e}")
        # Use a fallback simple matching algorithm
        matched_courses = []
        # We need to define a fallback approach here
        
        return render_template('recommendations.html', title="Your Course Recommendations", 
                              courses=matched_courses, interests=preferences.get('interests', []))



@app.route('/courses')
def course_list():
    search_query = request.args.get('search', '').lower()
    try:
        with open("data/courses_sampled.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            courses = data["veranstaltungen"]["veranstaltung"]
            # Normalize schlagwort to always be a list
            for course in courses:
                if not isinstance(course.get('schlagwort'), list):
                    course['schlagwort'] = []
            # Filter courses
            if search_query:
                courses = [
                    course for course in courses
                    if search_query in course['name'].lower() or
                       any(search_query in str(tag).lower() for tag in course['schlagwort'])
                ]
    except Exception as e:
        flash(f"Error loading courses: {e}")
        courses = []
    
    return render_template('courses.html', title="All Courses", courses=courses)

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    try:
        with open("data/courses_sampled.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            courses = data["veranstaltungen"]["veranstaltung"]
            course = next((c for c in courses if c['id'] == course_id), None)
    except Exception:
        course = None
    
    if not course:
        flash('Course not found!')
        return redirect(url_for('course_list'))
    
    return render_template('course_detail.html', title=course['name'], course=course)

@app.route('/about')
def about():
    return render_template('about.html', title="About Us")

if __name__ == '__main__':
    app.run(debug=True)