import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import os
import pickle

MODEL_FILE = "data/local_model.pkl"
TRAIN_DATA = "data/training_data.csv"

def train_local_model():
    if not os.path.exists(TRAIN_DATA):
        return None
    
    df = pd.read_csv(TRAIN_DATA)
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', ngram_range=(1, 2))),
        ('clf', LogisticRegression())
    ])
    
    pipeline.fit(df['text'], df['label'])
    
    # Ensure data directory exists
    if not os.path.exists("data"):
        os.makedirs("data")
        
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(pipeline, f)
    
    return pipeline

def get_local_prediction(text):
    if not os.path.exists(MODEL_FILE):
        model = train_local_model()
    else:
        with open(MODEL_FILE, 'rb') as f:
            model = pickle.load(f)
            
    if model is None:
        return {"error": "Local model training data not found."}
        
    prediction = model.predict([text])[0]
    proba = model.predict_proba([text])[0]
    
    label = "REAL" if prediction == 1 else "FAKE"
    confidence = proba[prediction] * 100
    
    return {
        "label": label,
        "confidence": confidence,
        "model_used": "Local Fallback Model (TF-IDF)"
    }
