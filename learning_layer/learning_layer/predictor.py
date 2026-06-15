import numpy as np
from core.db import get_connection, DB_PATH


class Predictor:
    def __init__(self, db_path=None):
        self._model = None
        self.db_path = db_path

    def train(self):
        from sklearn.ensemble import RandomForestClassifier
        conn = get_connection(self.db_path)
        rows = conn.execute(
            "SELECT price, engagement, llm_tier_used, converted FROM outcomes WHERE converted IS NOT NULL"
        ).fetchall()
        conn.close()
        if len(rows) < 10:
            return
        X = []
        y = []
        for r in rows:
            features = [r["price"], r["engagement"] or 0]
            tier = {"bulk": 0, "standard": 1, "priority": 2}.get(r["llm_tier_used"], 1)
            features.append(tier)
            X.append(features)
            y.append(r["converted"])
        self._model = RandomForestClassifier(n_estimators=100, random_state=42)
        self._model.fit(X, y)

    def predict_conversion(self, price, engagement, llm_tier):
        if self._model is None:
            self.train()
        if self._model is None:
            return None
        tier = {"bulk": 0, "standard": 1, "priority": 2}.get(llm_tier, 1)
        return self._model.predict_proba([[price, engagement, tier]])[0][1]
