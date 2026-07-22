"""
OCR Agent — EasyOCR / Tesseract fallback
Handles scanned images and image-based PDFs
"""
import os
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

_ocr_reader = None


def get_ocr_reader():
    """Lazy-load EasyOCR (heavy model download on first use)"""
    global _ocr_reader
    if _ocr_reader is None:
        try:
            import easyocr
            _ocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            logger.info("✅ EasyOCR initialized")
        except Exception as e:
            logger.warning(f"EasyOCR init failed: {e}. Will try pytesseract.")
            _ocr_reader = "tesseract"
    return _ocr_reader


def ocr_image(image_path: str) -> str:
    """Run OCR on an image file"""
    reader = get_ocr_reader()

    if reader == "tesseract":
        return _tesseract_ocr(image_path)

    try:
        results = reader.readtext(image_path, detail=0, paragraph=True)
        text = "\n".join(results)
        logger.info(f"OCR extracted {len(text)} chars from {Path(image_path).name}")
        return text
    except Exception as e:
        logger.error(f"EasyOCR failed on {image_path}: {e}")
        return _tesseract_ocr(image_path)


def _tesseract_ocr(image_path: str) -> str:
    """Fallback to pytesseract"""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        logger.error(f"Tesseract also failed: {e}")
        return "[OCR failed — could not extract text from image]"


def ocr_pdf(pdf_path: str) -> str:
    """Convert PDF pages to images, then OCR each page"""
    try:
        import pypdf
        import tempfile
        from PIL import Image
        import io

        reader = pypdf.PdfReader(pdf_path)
        all_text = []

        for page_num, page in enumerate(reader.pages):
            # Try to get images from the page
            if hasattr(page, "images") and page.images:
                for img_obj in page.images:
                    try:
                        img_bytes = img_obj.data
                        img = Image.open(io.BytesIO(img_bytes))
                        # Save temp and OCR (cross-platform)
                        temp_path = os.path.join(tempfile.gettempdir(), f"iki_page_{page_num}.png")
                        img.save(temp_path)
                        text = ocr_image(temp_path)
                        all_text.append(text)
                        os.remove(temp_path)
                    except Exception:
                        pass

        return "\n".join(all_text) if all_text else "[No text found via OCR]"
    except Exception as e:
        logger.error(f"PDF OCR error: {e}")
        return "[PDF OCR failed]"


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """OCR from raw bytes"""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name
    try:
        return ocr_image(tmp_path)
    finally:
        os.unlink(tmp_path)
