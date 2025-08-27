# src/doc_processor/utils.py

import os
import base64
import ollama
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from docx2pdf import convert
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load configuration from environment variables
OLLAMA_HOST = os.getenv('OLLAMA_HOST')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')

def image_to_base64(image_path: str):
    """Reads an image file and converts it to a Base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Failed to convert image to Base64: {e}")
        return None

def extract_text_with_gemma_vision(image_path: str):
    """Sends an image (as Base64) to the Gemma model for text extraction."""
    if not OLLAMA_MODEL or not OLLAMA_HOST:
        error_msg = "Error: OLLAMA_MODEL or OLLAMA_HOST environment variables are not set. Please check your .env file."
        print(error_msg)
        return ""

    print(f"Converting {os.path.basename(image_path)} to Base64...")
    base64_image = image_to_base64(image_path)
    if not base64_image:
        return ""

    print(f"Contacting ({OLLAMA_MODEL}) to extract text from image...")
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        prompt = "Transcribe all text in this image with high accuracy. Preserve the original line and paragraph formatting. Do not add any text other than what is in the input file."
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            options={"temperature": 0.0},
            images=[base64_image],
        )
        print("Text extraction with Gemma Vision successful.")
        return response['response']
    except Exception as e:
        print(f"Error contacting Gemma with image: {e}")
        return ""

def is_pdf_scanned(file_path: str):
    """Detects if a PDF has no extractable text layer."""
    try:
        doc = fitz.open(file_path)
        total_text_length = sum(len(page.get_text()) for page in doc)
        return total_text_length < 100
    except Exception as e:
        print(f"Error checking PDF: {e}")
        return True

def create_searchable_pdf(text_content: str, output_path: str):
    """Creates a new, searchable PDF file from text content, with improved margin handling."""
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    left_margin = 72
    right_margin = width - 72
    top_margin = height - 72
    bottom_margin = 72
    line_height = 12
    font_size = 10

    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        font_name = 'DejaVuSans'
    except Exception:
        print("Warning: DejaVuSans.ttf not found. Using standard font (Helvetica).")
        font_name = 'Helvetica'

    c.setFont(font_name, font_size)

    textobject = c.beginText()
    textobject.setTextOrigin(left_margin, top_margin)
    textobject.setFont(font_name, font_size)

    current_y = top_margin

    styles = getSampleStyleSheet()
    style = styles['Normal']
    style.fontName = font_name
    style.fontSize = font_size
    style.leading = line_height
    style.alignment = TA_LEFT
    style.leftIndent = 0
    style.rightIndent = 0

    paragraphs = text_content.split('\n')

    for para_text in paragraphs:
        p = Paragraph(para_text, style)
        available_width = width - left_margin - (width - right_margin)
        frame_height = p.wrap(available_width, height)[1]

        if current_y - frame_height < bottom_margin:
            c.drawText(textobject)
            c.showPage()
            textobject = c.beginText()
            textobject.setTextOrigin(left_margin, top_margin)
            textobject.setFont(font_name, font_size)
            current_y = top_margin

        current_y -= frame_height
        p.drawOn(c, left_margin, current_y)
        current_y -= line_height / 2

    c.drawText(textobject)
    c.save()
    print(f"Searchable PDF successfully created at: {output_path}")