import numpy as np
from core.db import get_connection, DB_PATH


class Embedder:
    def __init__(self):
        self._model = None
        self._model_name = "all-MiniLM-L6-v2"

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)

    def embed(self, text):
        self._load_model()
        return self._model.encode(text).tolist()

    def find_similar(self, text, top_k=5, db_path=None):
        conn = get_connection(db_path)
        rows = conn.execute(
            "SELECT id, content_summary, embedding, niche, price, converted FROM outcomes WHERE embedding IS NOT NULL"
        ).fetchall()
        conn.close()
        if not rows:
            return []
        vec = self.embed(text)
        scores = []
        for row in rows:
            stored = np.frombuffer(bytes(row["embedding"]), dtype=np.float32)
            sim = np.dot(vec, stored) / (np.linalg.norm(vec) * np.linalg.norm(stored) + 1e-10)
            scores.append((sim, dict(row)))
        scores.sort(key=lambda x: -x[0])
        return scores[:top_k]
