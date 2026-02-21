import easyocr
import numpy as np
from PIL import Image

def extract_text_from_image(image_file):
    try:
        # Initialize reader (this might take time on first run as it downloads models)
        reader = easyocr.Reader(['en'])
        
        # Convert streamlit file to numpy array
        image = Image.open(image_file)
        image_np = np.array(image)
        
        # Perform OCR
        results = reader.readtext(image_np)
        
        # Join all detected text
        extracted_text = " ".join([res[1] for res in results])
        
        return {
            "text": extracted_text,
            "snippet": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
        }
    except Exception as e:
        return {"error": str(e)}
