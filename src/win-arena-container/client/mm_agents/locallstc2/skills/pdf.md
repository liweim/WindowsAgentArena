---
name: pdf
domain: pdf
priority: high
when_to_use: Load when the contents of a PDF file stored in the VM must be read or understood
---

# Skill: PDF text extraction

- You must use `PdfTools.extract_text(vm_path=...)` before ordinary task actions whenever the task provides a PDF whose contents must be read, summarized, searched, or copied. Use the returned text as task evidence instead of reading the document visually page by page.
- Pass the absolute VM path, not a `file://` URL. In API calls, write Windows paths with forward slashes, for example `C:/Users/Docker/Desktop/document.pdf`. Do not put a path such as `C:\Users\...` in a normal Python string because backslash sequences can make the call fail to parse.
- If the exact filename is not stated, inspect the browser's local-file URL or use a read-only file listing to find the PDF before calling the API; do not guess the filename.
- The API extracts the complete embedded text layer in page order and returns plain text. It does not perform OCR; a scanned image-only PDF will return an explicit error.
- Preserve exact names, email addresses, dates, codes, amounts, and other task-critical details when using the extracted text in another app. Verify the final result before terminating.
