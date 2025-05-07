# app.py
from flask import Flask, request, render_template, redirect, url_for
from app.processor import process_user_inputs
from app.assets_loader import AssetLoader
import os
 
app = Flask(__name__)

@app.route("/courses", methods=["GET", "POST"])
def course_list():
    loader = AssetLoader(
        model_path=os.path.abspath("app/saved_sentence_transformer_model"),
        df_path=os.path.abspath("app/Processed_data_for_app.pkl"),
        embeddings_path=os.path.abspath("app/course_embeddings.npy")
    )

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
                model=loader.get_model(),
                df=loader.get_dataframe(),
                course_embeddings=loader.get_embeddings()
            )
        except Exception as e:
            error_msg = f"Search failed: {e}"
            results_df = loader.get_dataframe()
            return render_template("courses.html", courses=results_df.to_dict(orient="records"), error=error_msg)

        return render_template("courses.html", courses=results_df.to_dict(orient="records"))

    # Default GET: show full course list
    full_df = loader.get_dataframe()
    return render_template("courses.html", courses=full_df.to_dict(orient="records"))

@app.route("/")
def home():
    return redirect(url_for("course_list"))

if __name__ == "__main__":
    app.run(debug=True)
