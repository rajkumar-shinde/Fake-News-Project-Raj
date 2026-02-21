# Fake News Detector Website

A professional, human-designed web application to verify news headlines, URLs, articles, and social media posters using AI classification and live fact-checking.

## Features
- **Multi-Source Detection**: Support for Headlines, URLs (with scraping), Text, and Images (OCR).
- **AI-Powered**: Uses Hugging Face BERT-based models for classification.
- **Fact-Check Integration**: Cross-references claims with Google Fact Check Tools API.
- **OCR Support**: Extracts text from screenshots and posters using EasyOCR.
- **History Tracking**: Automatically saves detections to an SQLite database.
- **PDF Reports**: Export detailed analysis reports as PDFs.
- **Custom UI**: Professional design with custom CSS and a clean layout.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd fake-news-website
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Setup environment variables:
   Create a `.env` file in the root directory and add your API tokens:
   ```env
   HF_API_TOKEN=your_huggingface_token
   FACTCHECK_API_KEY=your_google_factcheck_key
   ```

## Running the App

Execute the following command to start the Streamlit server:
```bash
streamlit run app.py
```

## Project Structure
- `app.py`: Main application entry point and UI logic.
- `static/style.css`: Custom CSS for professional styling.
- `utils/`:
  - `hf_api.py`: Hugging Face Inference API integration.
  - `factcheck_api.py`: Google Fact Check API integration.
  - `url_extract.py`: Web scraping for article extraction.
  - `ocr_extract.py`: Image text extraction using EasyOCR.
  - `db.py`: SQLite database operations.
  - `pdf_report.py`: PDF report generation using ReportLab.
- `data/`:
  - `history.db`: SQLite database file (auto-generated).
  - `suspicious_words.txt`: List of keywords for heuristic analysis.

## Disclaimer
This tool uses AI and external APIs for prediction. It is intended for informational purposes and does not guarantee 100% accuracy. Always cross-verify information with multiple reputable sources.
