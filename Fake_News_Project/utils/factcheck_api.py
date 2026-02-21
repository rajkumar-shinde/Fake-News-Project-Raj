import requests
import os
from dotenv import load_dotenv

load_dotenv()
import streamlit as st
FACTCHECK_API_KEY = st.secrets.get("FACTCHECK_API_KEY", os.getenv("FACTCHECK_API_KEY"))
BASE_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

def check_fact(query):
    if not FACTCHECK_API_KEY:
        return {"error": "Google Fact Check API Key not found."}
    
    params = {
        "query": query,
        "key": FACTCHECK_API_KEY,
        "languageCode": "en-US"
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        claims = data.get("claims", [])
        results = []
        
        # Limit to top 3 results
        for claim in claims[:3]:
            claim_text = claim.get("text", "No text")
            claim_reviews = claim.get("claimReview", [])
            if claim_reviews:
                review = claim_reviews[0]
                results.append({
                    "claim": claim_text,
                    "publisher": review.get("publisher", {}).get("name", "Unknown"),
                    "rating": review.get("textualRating", "No rating"),
                    "url": review.get("url", "#")
                })
        
        return results
    except Exception as e:
        return {"error": str(e)}
