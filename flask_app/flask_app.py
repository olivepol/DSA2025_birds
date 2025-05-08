from flask import Flask, render_template, request
from app.processor import process_user_inputs
from app.assets_loader import AssetLoader
import pandas as pd
import os
import sys
from werkzeug.datastructures import MultiDict

# Ensure UTF-8 output in terminal/logs
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title="Course Matcher - Volkshochschule Berlin")


@app.route("/courses", methods=["GET", "POST"])
def course_list():
    loader = AssetLoader(df_path=os.path.abspath("app/data/Processed_data_for_app.pkl"))
    df = loader.get_dataframe()

    if request.method == "POST":
        try:
            user_query = request.form.get("search", "")
            budget_input = request.form.get("budget", "").strip()
            user_budget = float(budget_input) if budget_input else 0
            user_gender = request.form.get("gender", "")
            target_groups = request.form.getlist("target_group")

            results_df = process_user_inputs(
                user_query=user_query,
                user_budget=user_budget,
                user_gender=user_gender,
                user_target_groups=target_groups,
                df=df
            )

            return render_template(
                "courses.html",
                courses=results_df.to_dict(orient="records"),
                form_data=request.form  # Preserves form values
            )

        except Exception as e:
            error_msg = f"Search failed: {e}"
            empty_df = pd.DataFrame()
            return render_template(
                "courses.html",
                courses=empty_df.to_dict(orient="records"),
                error=error_msg,
                form_data=request.form  # Re-populate form after failure
            )

    # GET request: show full list
    return render_template(
        "courses.html",
        courses=df.to_dict(orient="records"),
        form_data=MultiDict()  # Empty but safe for .getlist() in template
    )


@app.route('/about')
def about():
    return render_template('about.html', title="About Us")


if __name__ == '__main__':
    app.run(debug=True)
