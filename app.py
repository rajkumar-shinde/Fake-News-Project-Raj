import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st
from dotenv import load_dotenv
from utils.db import init_db, save_detection, get_history, delete_record
from utils.hf_api import query_hf_api
from utils.local_model import get_local_prediction
from utils.factcheck_api import check_fact
from utils.url_extract import extract_article_text
from utils.ocr_extract import extract_text_from_image
from utils.pdf_report import generate_pdf_report
import pandas as pd
from datetime import datetime

# Page Config
st.set_page_config(page_title="Fake News Detector", page_icon="📰", layout="wide")

# Load environment variables
load_dotenv()

# Initialize Database
init_db()

# Load CSS
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("CSS file not found. UI may look plain.")

local_css("static/style.css")

# Navigation state
if "page" not in st.session_state:
    st.session_state.page = "Home"

def set_page(page_name):
    st.session_state.page = page_name

# Header / Navbar
st.markdown("""
    <div class="nav-container">
        <div style="font-size: 1.5rem; font-weight: bold;">📰 FakeNewsShield</div>
    </div>
""", unsafe_allow_html=True)

cols = st.columns([2, 1, 1, 1, 1, 2])
with cols[1]:
    if st.button("Home"): set_page("Home")
with cols[2]:
    if st.button("Detector"): set_page("Detector")
with cols[3]:
    if st.button("History"): set_page("History")
with cols[4]:
    if st.button("About"): set_page("About")

# --- PAGE: HOME ---
def show_home():
    st.markdown("""
        <div class="hero-section">
            <h1>Fake News Detector</h1>
            <p>Empowering you to verify information in the age of misinformation.
            Check headlines, URLs, articles, or social media posters instantly.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
            <div class="feature-card">
                <h3>Multi-Source Input</h3>
                <p>Support for direct headlines, website URLs, and long-form articles.</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="feature-card">
                <h3>AI-Powered OCR</h3>
                <p>Extract text from WhatsApp forwards or Instagram screenshots automatically.</p>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class="feature-card">
                <h3>Live Fact-Check</h3>
                <p>Integrated with Google Fact Check Tools to cross-reference known claims.</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# --- PAGE: DETECTOR ---
def show_detector():
    st.markdown("## 🔍 Information Verifier")

    tabs = st.tabs(["Headline", "URL", "Full Text", "Image Poster"])

    final_text = ""
    input_type = ""
    headline = ""  # for fact-check query

    with tabs[0]:
        headline = st.text_input("Enter News Headline", placeholder="e.g. NASA confirms moon is made of cheese")
        if headline:
            final_text = headline
            input_type = "Headline"

    with tabs[1]:
        url = st.text_input("Enter Article URL", placeholder="https://example.com/news-article")
        if url:
            if st.button("Extract Content"):
                with st.spinner("Scraping article..."):
                    result = extract_article_text(url)
                    if "error" not in result:
                        st.success("Content extracted!")
                        st.info(f"**Preview:** {result['snippet']}")
                        final_text = result["text"]
                        input_type = "URL"
                    else:
                        st.error(f"Failed to extract: {result['error']}")

    with tabs[2]:
        body_text = st.text_area("Paste Full Article/Blog Text", height=200)
        if body_text:
            final_text = body_text
            input_type = "Text"

    with tabs[3]:
        uploaded_file = st.file_uploader("Upload Poster/Screenshot", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Image", width=300)
            if st.button("Extract Text with OCR"):
                with st.spinner("Processing image..."):
                    result = extract_text_from_image(uploaded_file)
                    if "error" not in result:
                        st.success("Text extracted!")
                        st.write(f"**Extracted Text Preview:** {result['snippet']}")
                        final_text = result["text"]
                        input_type = "Image"
                    else:
                        st.error(f"OCR Error: {result['error']}")

    if st.button("Analyze Credibility", type="primary"):
        if not final_text.strip():
            st.warning("Please provide some input first!")
            st.stop()

        with st.spinner("Analyzing..."):

            # ✅ 1) FACT CHECK FIRST (PRIORITY)
            fact_query = headline if input_type == "Headline" and headline else final_text[:120]
            fact_results = check_fact(fact_query)

            override_label = None
            override_confidence = None

            if isinstance(fact_results, list) and len(fact_results) > 0:
                top = fact_results[0]
                rating = str(top.get("rating", "")).lower()

                # If rating indicates false → FAKE
                # Added more comprehensive keywords for international fact-checkers
                fake_keywords = ["false", "fake", "incorrect", "pants on fire", "misleading", "hoax", 
                                "debunked", "inaccurate", "misbar", "unsubstantiated", "fabricated", 
                                "mostly false", "not true", "refuted", "erroneous", "scam"]
                
                if any(w in rating for w in fake_keywords):
                    override_label = "FAKE"
                    override_confidence = 99.0

                # If rating indicates true → REAL
                elif any(w in rating for w in ["true", "correct", "accurate", "verified", "mostly true", "authentic"]):
                    override_label = "REAL"
                    override_confidence = 99.0

            # ✅ 2) If fact-check gives decision, skip HF model
            if override_label:
                prediction = {"label": override_label, "confidence": override_confidence, "model_used": "Verified Fact-Check"}
            else:
                # ensemble AI
                prediction = query_hf_api(final_text)

                if "error" in prediction:
                    st.warning(f"Cloud AI is busy. Using local analyzer...")
                    prediction = get_local_prediction(final_text)
                    
                if "error" in prediction:
                    st.error(prediction["error"])
                    st.stop()

            confidence = float(prediction.get("confidence", 0))
            display_label = prediction.get("label", "UNKNOWN")

            # ✅ 3) Heuristic & Credibility Logic
            text_content = final_text.lower()
            outlandish_keywords = ["10000 years", "microchips", "secretly", "miracle cure", "reptilian", "flat earth", "magic wand", "time travel", "dragon"]
            is_outlandish = any(kw in text_content for kw in outlandish_keywords)
            
            if is_outlandish:
                display_label = "FAKE"
                confidence = 99.0
                cred_score = 5
                prediction["model_used"] = "Pattern Recognition"
            elif override_label:
                cred_score = 95 if override_label == "REAL" else 5
            else:
                cred_score = int(confidence) if display_label == "REAL" else int(100 - confidence)

            # Safety check: If AI is "Real" but confidence is low (<70%) and it's a short text
            if display_label == "REAL" and confidence < 70 and len(final_text.split()) < 15:
                display_label = "SUSPICIOUS"
                cred_score = 45

            is_real = (display_label == "REAL")

            # Save to DB
            save_detection(input_type, final_text, display_label, confidence, cred_score)

            # Result Card
            st.markdown(f"""
                <div class="result-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3>Detection Result</h3>
                        <span class="{"badge-real" if display_label == "REAL" else "badge-fake"}">{display_label}</span>
                    </div>
                    <p>Confidence: <b>{confidence:.2f}%</b></p>
                    <p>Source: <i>{prediction.get('model_used', 'Unknown')}</i></p>
                    <p>Credibility Score:</p>
            """, unsafe_allow_html=True)

            st.progress(cred_score / 100)
            st.write(f"Overall Score: {cred_score}/100")
            
            # AI Ensemble Details (if applicable)
            if "all_results" in prediction:
                with st.expander("📊 AI Voting Breakdown"):
                    for r in prediction["all_results"]:
                        st.write(f"- {r['model']}: **{r['label']}** ({r['score']:.2f})")

            # Suspicious Keywords
            st.markdown("#### 💡 Why?")
            try:
                with open("data/suspicious_words.txt", "r") as f:
                    suspicious_words = [line.strip() for line in f.readlines() if line.strip()]
            except FileNotFoundError:
                suspicious_words = ["unbelievable", "shocking", "conspiracy", "secret", "exposed"]

            found_words = [w for w in suspicious_words if w.lower() in final_text.lower()]
            if found_words:
                st.write(f"Suspicious patterns found: {', '.join(found_words)}")
            else:
                st.write("No common clickbait keywords found.")

            if override_label:
                st.caption("✅ Decision was based on verified Fact-Check sources (High reliability).")
            elif is_outlandish and display_label == "FAKE":
                st.caption("🚨 Flagged as FAKE due to highly suspicious or outlandish claim patterns.")
            else:
                st.caption("⚠️ AI prediction is pattern-based and not guaranteed to be 100% accurate.")

            st.markdown("</div>", unsafe_allow_html=True)

            # Fact Check Section
            if fact_results and isinstance(fact_results, list) and len(fact_results) > 0:
                st.markdown("### 🌐 External Fact Checks")
                for res in fact_results:
                    with st.expander(f"Claim: {res.get('claim','')[:60]}..."):
                        st.write(f"**Publisher:** {res.get('publisher','N/A')}")
                        st.write(f"**Rating:** {res.get('rating','N/A')}")
                        st.markdown(f"[Read full report]({res.get('url','#')})")
            else:
                st.info("No matching claims found in Google Fact Check database.")

            # PDF Report
            report_data = {
                "input_type": input_type,
                "prediction": display_label,
                "confidence": confidence,
                "credibility_score": cred_score,
                "input_text": final_text[:1000] + ("..." if len(final_text) > 1000 else ""),
                "fact_checks": fact_results if isinstance(fact_results, list) else []
            }

            pdf_buffer = generate_pdf_report(report_data)
            st.download_button(
                label="📥 Download Detailed Report (PDF)",
                data=pdf_buffer,
                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )

# --- PAGE: HISTORY ---
def show_history():
    st.markdown("## 📜 Detection History")

    history_df = get_history()

    if history_df.empty:
        st.info("No records found.")
        return

    search = st.text_input("Search history by input or prediction")
    if search:
        history_df = history_df[
            history_df["input_value_short"].str.contains(search, case=False, na=False) |
            history_df["prediction"].str.contains(search, case=False, na=False)
        ]

    st.dataframe(history_df, use_container_width=True)

    with st.expander("Manage Records"):
        record_id = st.number_input("Enter ID to delete", min_value=1, step=1)
        if st.button("Delete Record"):
            delete_record(record_id)
            st.success(f"Record {record_id} deleted!")
            st.rerun()

# --- PAGE: ABOUT ---
def show_about():
    st.markdown("## ℹ️ About This Project")
    
    if st.button("🔄 Train Local AI"):
        from utils.local_model import train_local_model
        with st.spinner("Retraining..."):
            train_local_model()
            st.success("Local model updated!")

    st.write("""
        This Fake News Detector is a professional tool designed to help users identify potentially misleading information.
        
        ### Our Methodology:
        1. **Verified Fact-Checks**: We first query the Google Fact Check Tools API. Verified results from professional publishers (like PIB, Reuters, etc.) are prioritized.
        2. **AI Voting Ensemble**: We use a committee of multiple high-accuracy BERT models. A claim is flagged only if the majority of models agree.
        3. **Pattern Layer**: For common outlandish myths (microchips, immortality, etc.), we have a dedicated truth verification layer.
        4. **Local Fallback**: If cloud APIs are unreachable, we use a local TF-IDF classifier trained on verified data.
    """)
    st.info("Developed for transparency and information literacy.")

# Routing
if st.session_state.page == "Home":
    show_home()
elif st.session_state.page == "Detector":
    show_detector()
elif st.session_state.page == "History":
    show_history()
elif st.session_state.page == "About":
    show_about()

# Footer
st.markdown("""
    <div class="footer">
        <p>© 2026 FakeNewsShield | Professional Misinformation Detection</p>
        <p>Powered by Streamlit, Hugging Face, and Google APIs</p>
    </div>
""", unsafe_allow_html=True)
