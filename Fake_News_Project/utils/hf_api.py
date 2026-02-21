import requests
import os
from dotenv import load_dotenv

load_dotenv()
import streamlit as st
HF_API_TOKEN = st.secrets.get("HF_API_TOKEN", os.getenv("HF_API_TOKEN"))


# ✅ Try models in order (fallback)
MODEL_IDS = [
    "Pulk17/Fake-News-Detection",
    "Hamad/fake-news-detection-model",
    "mrm8488/bert-tiny-finetuned-fake-news-detection",
    "therealcyberlord/fake-news-classification-distilbert",
    "llm-agents/fake-news-detector",
]

def _call_model(model_id: str, text: str):
    api_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": text}

    r = requests.post(api_url, headers=headers, json=payload, timeout=30)
    return r

def query_hf_api(text: str):
    if not HF_API_TOKEN:
        return {"error": "HF_API_TOKEN not found. Add it in .env file."}

    results = []
    
    for model_id in MODEL_IDS:
        try:
            response = _call_model(model_id, text)
            if response.status_code != 200:
                continue

            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                preds = result[0] if isinstance(result[0], list) else result
                top = max(preds, key=lambda x: x.get("score", 0))
                label = str(top.get("label", "UNKNOWN")).lower()
                score = float(top.get("score", 0))

                # Normalize labels for each model
                if "fake" in label or "label_0" in label or "false" in label:
                    mapped = "FAKE"
                elif "real" in label or "label_1" in label or "true" in label:
                    mapped = "REAL"
                else:
                    mapped = label.upper()
                
                results.append({"label": mapped, "score": score, "model": model_id})
        except:
            continue

    if not results:
        return {"error": "All AI models were temporarily unreachable. Please try again or use the local fallback."}

    # Voting System
    fake_votes = [r for r in results if r["label"] == "FAKE"]
    real_votes = [r for r in results if r["label"] == "REAL"]

    if len(fake_votes) >= len(real_votes):
        final_label = "FAKE"
        avg_confidence = sum([r["score"] for r in fake_votes]) / len(fake_votes) * 100
    else:
        final_label = "REAL"
        avg_confidence = sum([r["score"] for r in real_votes]) / len(real_votes) * 100

    return {
        "label": final_label,
        "confidence": avg_confidence,
        "model_used": f"AI Ensemble ({len(results)} models voted)",
        "all_results": results
    }
