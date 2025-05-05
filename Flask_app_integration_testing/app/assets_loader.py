import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

class AssetLoader:
    def __init__(self, model_path, df_path, embeddings_path):
        print("📦 [AssetLoader] Initializing...")
        print(f"📁 model_path: {model_path}")
        print(f"🔍 exists: {os.path.exists(model_path)}")
        if os.path.exists(model_path):
            print("📂 contents:", os.listdir(model_path))
        else:
            print("🚨 Model path not found!")

        print(f"📁 df_path: {df_path} — exists: {os.path.exists(df_path)}")
        print(f"📁 embeddings_path: {embeddings_path} — exists: {os.path.exists(embeddings_path)}")

        self.model = SentenceTransformer(model_path)
        self.df = pd.read_pickle(df_path)
        self.embeddings = np.load(embeddings_path)

    def get_model(self):
        return self.model

    def get_dataframe(self):
        return self.df.copy()

    def get_embeddings(self):
        return self.embeddings
