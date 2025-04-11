# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key in production

# Mock user database - replace with a real database in production
users = {}

# This would be replaced with your actual course data loading function
def load_course_data():
    try:
        # In production, you might load from a database or CSV file
        # courses_df = pd.read_csv('vhs_courses.csv')
        # For now, let's create some sample data
        courses = [
            {"id": 1, "title": "German A1", "category": "Language", "tags": ["beginner", "language", "german"]},
            {"id": 2, "title": "Yoga for Beginners", "category": "Health", "tags": ["yoga", "fitness", "beginner"]},
            {"id": 3, "title": "Introduction to Python", "category": "Technology", "tags": ["programming", "technology", "beginner"]},
            {"id": 4, "title": "Art History", "category": "Arts", "tags": ["art", "history", "culture"]}
        ]
        return courses
    except Exception as e:
        print(f"Error loading course data: {e}")
        return []

courses = load_course_data()

# Routes
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title="Course Matcher - Volkshochschule Berlin")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users:
            flash('Username already exists!')
            return redirect(url_for('register'))
        
        users[username] = {
            'password': generate_password_hash(password),
            'interests': []
        }
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html', title="Register")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username not in users or not check_password_hash(users[username]['password'], password):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        
        session['username'] = username
        return redirect(url_for('profile'))
    
    return render_template('login.html', title="Login")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = users[session['username']]
    return render_template('profile.html', title="Your Profile", user=user)

@app.route('/interests', methods=['GET', 'POST'])
def interests():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Process the submitted interests
        selected_interests = request.form.getlist('interests')
        users[session['username']]['interests'] = selected_interests
        
        flash('Your interests have been updated!')
        return redirect(url_for('recommendations'))
    
    # Categories of interests for the form
    interest_categories = {
        'Languages': ['German', 'English', 'Spanish', 'French', 'Italian', 'Other languages'],
        'Arts & Crafts': ['Painting', 'Drawing', 'Sculpture', 'Photography', 'Handicrafts'],
        'Health & Fitness': ['Yoga', 'Pilates', 'Meditation', 'Dancing', 'Sports'],
        'Technology': ['Programming', 'Web Development', 'Data Science', 'Digital Marketing'],
        'Other': ['Cooking', 'Music', 'Literature', 'History', 'Philosophy', 'Science']
    }
    
    return render_template('interests.html', title="Your Interests", categories=interest_categories)

@app.route('/recommendations')
def recommendations():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_interests = users[session['username']]['interests']
    
    # Simple matching algorithm
    # In a real application, you would use a more sophisticated approach
    matched_courses = []
    for course in courses:
        for tag in course['tags']:
            if tag.lower() in [interest.lower() for interest in user_interests]:
                matched_courses.append(course)
                break
    
    return render_template('recommendations.html', title="Your Course Recommendations", 
                          courses=matched_courses, interests=user_interests)

@app.route('/courses')
def course_list():
    try:
        with open("web-app/backend/data/courses.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            courses = data["veranstaltungen"]["veranstaltung"]
    except Exception as e:
        flash(f"Error loading courses: {e}")
        courses = []
    
    return render_template('courses.html', title="All Courses", courses=courses)

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    course = next((c for c in courses if c['id'] == course_id), None)
    
    if not course:
        flash('Course not found!')
        return redirect(url_for('course_list'))
    
    return render_template('course_detail.html', title=course['title'], course=course)

@app.route('/about')
def about():
    return render_template('about.html', title="About Us")

if __name__ == '__main__':
    app.run(debug=True)