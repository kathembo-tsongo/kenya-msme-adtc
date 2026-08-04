"""
ocr_extract.py -- Extract text from scanned/image PDFs using OCR
(for files where pypdf's normal text extraction returns nothing).
"""
import sys
from pathlib import Path

from pdf2image import convert_from_path
import pytesseract

def ocr_pdf(pdf_path: str, max_pages: int = None) -> str:
    print(f"Converting {pdf_path} to images...")
    images = convert_from_path(pdf_path, dpi=200)
    if max_pages:
        images = images[:max_pages]

    print(f"Running OCR on {len(images)} pages...")
    full_text = []
    for i, img in enumerate(images, 1):
        text = pytesseract.image_to_string(img)
        full_text.append(text)
        if i % 5 == 0 or i == len(images):
            print(f"  Processed {i}/{len(images)} pages")

    return "\n\n".join(full_text)


if __name__ == "__main__":
    targets = [
        "documents/kb2_tax_kra/kra_annual_revenue_2023_2024.pdf",
        "documents/kb8_national_policy_strategy/wef_services_report.pdf",
    ]

    for pdf_path in targets:
        text = ocr_pdf(pdf_path)
        out_path = pdf_path.replace(".pdf", "_ocr.txt")
        with open(out_path, "w") as f:
            f.write(text)
        print(f"Saved OCR text ({len(text)} chars) to {out_path}\n")
