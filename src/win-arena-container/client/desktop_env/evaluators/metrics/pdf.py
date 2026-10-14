import operator
import os
from typing import Any
from typing import Dict

import fitz  # PyMuPDF
from pypdf import PdfReader

from .general import check_text_points


def check_pdf_pages(pdf_file: str, rules: Dict[str, Any]) -> float:
    if pdf_file is None:
        return 0.0
    reader = PdfReader(pdf_file)
    nb_pages: int = len(reader.pages)
    return float(getattr(operator, rules["relation"])(nb_pages, rules["ref_value"]))


def check_pdf_text_points(pdf_file: str, rules: Dict[str, Any]) -> float:
    """Check required text facts in a PDF downloaded from the guest.

    Extraction runs in the evaluator environment so scoring does not depend on
    optional Python packages being installed inside the Windows VM.
    """
    if not pdf_file or not os.path.isfile(pdf_file):
        return 0.0

    try:
        with fitz.open(pdf_file) as document:
            text = "\n".join(page.get_text() for page in document)
    except Exception:
        return 0.0

    return check_text_points(text, rules)


def extract_answers_from_pdf(pdf_file):
    doc = fitz.open(pdf_file)
    answers = []

    for page in doc:
        text = page.get_text()
        lines = text.split('\n')
        for line in lines:
            if line.strip():
                parts = line.split('=')
                if len(parts) > 1:
                    answer = parts[-1].strip()
                    answers.append(answer)

    return answers
