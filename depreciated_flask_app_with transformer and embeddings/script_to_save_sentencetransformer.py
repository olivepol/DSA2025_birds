
from sentence_transformers import SentenceTransformer


# 1. Load German-compatible model
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
model.save("saved_sentence_transformer_model")

#please load this, and to run the app, save the model in Flask_app>app folder