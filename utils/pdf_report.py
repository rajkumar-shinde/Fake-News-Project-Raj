from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO
from datetime import datetime

def generate_pdf_report(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("Fake News Detection Report", styles['Title']))
    story.append(Spacer(1, 12))

    # Meta Info
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Date: {timestamp}", styles['Normal']))
    story.append(Spacer(1, 24))

    # Analysis Results
    story.append(Paragraph("Analysis Results", styles['Heading2']))
    story.append(Spacer(1, 12))

    results_data = [
        ["Field", "Value"],
        ["Input Type", data.get("input_type", "N/A")],
        ["Prediction", data.get("prediction", "N/A")],
        ["Confidence", f"{data.get('confidence', 0):.2f}%"],
        ["Credibility Score", f"{data.get('credibility_score', 0)}/100"]
    ]
    
    table = Table(results_data, colWidths=[150, 350])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 24))

    # Extracted Text Preview
    story.append(Paragraph("Extracted/Input Text Preview", styles['Heading2']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(data.get("input_text", "N/A"), styles['Italic']))
    story.append(Spacer(1, 24))

    # Fact Check Results
    if data.get("fact_checks"):
        story.append(Paragraph("Google Fact Check Results", styles['Heading2']))
        story.append(Spacer(1, 12))
        for res in data["fact_checks"]:
            story.append(Paragraph(f"<b>Claim:</b> {res['claim']}", styles['Normal']))
            story.append(Paragraph(f"<b>Publisher:</b> {res['publisher']} | <b>Rating:</b> {res['rating']}", styles['Normal']))
            story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return buffer
