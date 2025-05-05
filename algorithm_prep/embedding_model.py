# embedding_model.py

import numpy as np
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import os

class EmbeddingModel:
    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2', 
                 model_path: Optional[str] = None):
        """Initialize the embedding model.
        
        Args:
            model_name: Name of the pre-trained model to use.
            model_path: Path to a saved model.
        """
        self.model_name = model_name
        self.model_path = model_path
        self.model = None
        
    def load_model(self) -> SentenceTransformer:
        """Load the sentence transformer model."""
        if self.model_path and os.path.exists(self.model_path):
            self.model = SentenceTransformer(self.model_path)
        else:
            self.model = SentenceTransformer(self.model_name)
        return self.model
    
    def save_model(self, path: str) -> None:
        """Save the model to the specified path."""
        if self.model:
            self.model.save(path)
    
    def encode_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Encode a list of texts into embeddings."""
        if not self.model:
            self.load_model()
        return self.model.encode(texts, batch_size=batch_size, show_progress_bar=True)
    
    def save_embeddings(self, embeddings: np.ndarray, path: str) -> None:
        """Save embeddings to a numpy file."""
        np.save(path, embeddings)
    
    def load_embeddings(self, path: str) -> np.ndarray:
        """Load embeddings from a numpy file."""
        return np.load(path)