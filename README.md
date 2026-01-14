# PDF OCR Tool

Simple PDF OCR app with a GUI that allows you to extract text from PDF documents using multiple OCR engines.

## Features

- **Import PDF** - Open any PDF file for viewing
- **OCR by Page** - Extract text from the currently displayed page
- **OCR by Selection** - Click and drag to draw a rectangle, then OCR just that area
- **OCR Entire Document** - Process all pages in the PDF
- **Multiple OCR Engines** - Choose between Tesseract, EasyOCR, or Windows OCR
- **Zoom & Navigate** - Zoom in/out and navigate between pages
- **Save Output** - Export extracted text to a file

## OCR Engines

| Engine | Description | Best For |
|--------|-------------|----------|
| **Tesseract** | Traditional OCR, fast and accurate, 100+ languages | General documents, printed text |
| **EasyOCR** | Deep learning-based, handles complex layouts | Handwriting, curved text, complex backgrounds |
| **Windows OCR** | Built-in Windows 10/11 engine, very fast | Quick extraction, no extra installation |

## Requirements

- Python 3.8+
- Windows 10/11 (for Windows OCR)
- Tesseract OCR (optional, for Tesseract engine)

## Installation

1. Clone or download this repository

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional)** Install Tesseract OCR for the Tesseract engine:
   
   **Windows:**
   ```bash
   winget install UB-Mannheim.TesseractOCR
   ```
   
   **Untested**

   **macOS:**
   ```bash
   brew install tesseract
   ```
   
   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt install tesseract-ocr
   ```

## Usage

Run the application:
```bash
python ocr_app.py
```

### Controls

1. **Open PDF** - Click to browse and select a PDF file
2. **Navigation** - Use Prev/Next buttons to navigate pages
3. **Zoom** - Zoom in/out for better viewing
4. **OCR Engine** - Select from dropdown: Tesseract, EasyOCR, or Windows OCR
5. **OCR Current Page** - Extract text from the visible page
6. **OCR Selection** - Click and drag on the PDF to select an area, then click this button
7. **OCR Entire Document** - Process all pages (may take a while for large documents)
8. **Clear Selection** - Remove the selection rectangle
9. **Save Text** - Save the extracted text to a file

## Tips

- **EasyOCR** takes a moment to load the first time (downloads ~50MB model)
- **Windows OCR** requires no extra installation on Windows 10/11
- For better OCR results, zoom in on the page before processing
- Use selection OCR for specific areas like tables or columns
- The OCR output panel supports copy/paste (Ctrl+C, Ctrl+V)
- Compare results from different engines to find the best one for your document

## Libraries & References

This application was built using the following open-source libraries:

| Library | License | Source |
|---------|---------|--------|
| **PyMuPDF (fitz)** | AGPL-3.0 | https://github.com/pymupdf/PyMuPDF |
| **pytesseract** | Apache-2.0 | https://github.com/madmaze/pytesseract |
| **Tesseract OCR** | Apache-2.0 | https://github.com/tesseract-ocr/tesseract |
| **EasyOCR** | Apache-2.0 | https://github.com/JaidedAI/EasyOCR |
| **winocr** | MIT | https://github.com/GitHub30/winocr |
| **Pillow** | HPND | https://github.com/python-pillow/Pillow |
| **Tkinter** | PSF | https://docs.python.org/3/library/tkinter.html |

### Additional Resources

- [Tesseract Documentation](https://tesseract-ocr.github.io/)
- [EasyOCR Supported Languages](https://www.jaided.ai/easyocr/)
- [Windows OCR Languages](https://learn.microsoft.com/en-us/windows/uwp/audio-video-camera/ocr)
