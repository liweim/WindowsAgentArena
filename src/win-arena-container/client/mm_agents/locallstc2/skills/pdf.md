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
- The API extracts the complete embedded text layer in page order. Every page begins with a marker such as `===== PDF PAGE 7 =====`, so a text-search result can be mapped back to its PDF page.
- Extracted text up to 1000 characters is returned directly. Longer text overwrites one fixed local text file: `C:/Users/Docker/Desktop/pdf.txt` on Windows, `/home/user/pdf.txt` on Linux, or `/sdcard/Download/pdf.txt` on Android. Use `bash_execution` to search that exact path for targeted keywords or patterns and limit the output; never print the whole file into context.
- `PdfTools.extract_text` does not render images. Start with text because it is faster and searchable.
- **Mandatory for every PDF:** after extracting or searching PDF text, you must call `PdfTools.render_page(vm_path=..., page_number=...)` for every page that supports the intended answer or output. You must visually inspect the rendered page before writing the PDF-derived result or terminating. This requirement applies even when the PDF is short, plain, or the extracted text appears unambiguous; text extraction alone is never sufficient verification.
- The image uses a one-based name such as `page_0007.png` in the fixed `pdf_pages` directory reported by the API. `render_page` returns this image directly as the first visual input on the next model turn, so inspect that image before using the value. Do not open Paint or another image viewer.
- `render_page` defaults to 144 DPI and accepts 72 through 300 DPI; use a higher value only for small print.
- The API does not perform OCR; a scanned image-only PDF will return an explicit error.
- Preserve exact names, email addresses, dates, codes, amounts, and other task-critical details when using the extracted text in another app. Verify the final result before terminating.
