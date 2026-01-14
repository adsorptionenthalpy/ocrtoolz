"""
Simple PDF OCR Application
- Import PDF files
- OCR by page, by selection, or entire document
- Multiple OCR engines: Tesseract, EasyOCR, Windows OCR
serpentchain
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageTk
import io
import threading
import numpy as np

# Set Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Lazy load OCR engines
_easyocr_reader = None
_winocr_available = None


def get_easyocr_reader():
    """Lazy load EasyOCR reader (takes time to initialize)"""
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        _easyocr_reader = easyocr.Reader(['en'], gpu=False)
    return _easyocr_reader


def check_winocr_available():
    """Check if Windows OCR is available"""
    global _winocr_available
    if _winocr_available is None:
        try:
            import winocr
            _winocr_available = True
        except ImportError:
            _winocr_available = False
    return _winocr_available


class OCREngine:
    """OCR Engine wrapper for different backends"""
    
    TESSERACT = "Tesseract"
    EASYOCR = "EasyOCR"
    WINDOWS_OCR = "Windows OCR"
    
    @staticmethod
    def get_available_engines():
        """Return list of available OCR engines"""
        engines = [OCREngine.TESSERACT]
        
        try:
            import easyocr
            engines.append(OCREngine.EASYOCR)
        except ImportError:
            pass
            
        try:
            import winocr
            engines.append(OCREngine.WINDOWS_OCR)
        except ImportError:
            pass
            
        return engines
    
    @staticmethod
    def perform_ocr(image, engine_name):
        """Perform OCR using the specified engine"""
        if engine_name == OCREngine.TESSERACT:
            return OCREngine._tesseract_ocr(image)
        elif engine_name == OCREngine.EASYOCR:
            return OCREngine._easyocr_ocr(image)
        elif engine_name == OCREngine.WINDOWS_OCR:
            return OCREngine._windows_ocr(image)
        else:
            raise ValueError(f"Unknown OCR engine: {engine_name}")
    
    @staticmethod
    def _tesseract_ocr(image):
        """Perform OCR using Tesseract"""
        return pytesseract.image_to_string(image)
    
    @staticmethod
    def _easyocr_ocr(image):
        """Perform OCR using EasyOCR"""
        reader = get_easyocr_reader()
        # Convert PIL Image to numpy array
        img_array = np.array(image)
        results = reader.readtext(img_array, detail=0, paragraph=True)
        return '\n'.join(results)
    
    @staticmethod
    def _windows_ocr(image):
        """Perform OCR using Windows OCR"""
        import winocr
        import asyncio
        
        # Run async OCR
        async def do_ocr():
            result = await winocr.recognize_pil(image, 'en')
            return result.text
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(do_ocr())


class PDFOCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF OCR Tool")
        self.root.geometry("1200x800")
        
        self.pdf_document = None
        self.current_page = 0
        self.total_pages = 0
        self.current_image = None
        self.photo_image = None
        self.selection_start = None
        self.selection_rect = None
        self.zoom_level = 1.0
        
        # OCR engine selection
        self.available_engines = OCREngine.get_available_engines()
        self.selected_engine = tk.StringVar(value=self.available_engines[0])
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top toolbar - Row 1
        toolbar1 = ttk.Frame(main_frame)
        toolbar1.pack(fill=tk.X, pady=(0, 2))
        
        ttk.Button(toolbar1, text="Open PDF", command=self.open_pdf).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar1, text="◀ Prev", command=self.prev_page).pack(side=tk.LEFT, padx=2)
        self.page_label = ttk.Label(toolbar1, text="Page: 0 / 0")
        self.page_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar1, text="Next ▶", command=self.next_page).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar1, text="Zoom +", command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar1, text="Zoom -", command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        self.zoom_label = ttk.Label(toolbar1, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(toolbar1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar1, text="Clear Selection", command=self.clear_selection).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar1, text="Save Text", command=self.save_text).pack(side=tk.LEFT, padx=2)
        
        # Top toolbar - Row 2 (OCR controls)
        toolbar2 = ttk.Frame(main_frame)
        toolbar2.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(toolbar2, text="OCR Engine:").pack(side=tk.LEFT, padx=(2, 5))
        
        engine_combo = ttk.Combobox(
            toolbar2, 
            textvariable=self.selected_engine,
            values=self.available_engines,
            state="readonly",
            width=15
        )
        engine_combo.pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar2, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(toolbar2, text="OCR Current Page", command=self.ocr_current_page).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar2, text="OCR Selection", command=self.ocr_selection).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar2, text="OCR Entire Document", command=self.ocr_entire_document).pack(side=tk.LEFT, padx=2)
        
        # Engine info label
        self.engine_info = ttk.Label(toolbar2, text="", foreground="gray")
        self.engine_info.pack(side=tk.RIGHT, padx=5)
        self.update_engine_info()
        engine_combo.bind("<<ComboboxSelected>>", lambda e: self.update_engine_info())
        
        # Content area with paned window
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - PDF viewer
        left_frame = ttk.LabelFrame(paned, text="PDF Preview")
        paned.add(left_frame, weight=2)
        
        # Canvas with scrollbars for PDF display
        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="gray", cursor="cross")
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind mouse events for selection
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        
        # Right panel - OCR text output
        right_frame = ttk.LabelFrame(paned, text="OCR Output")
        paned.add(right_frame, weight=1)
        
        self.text_output = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.text_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready. Open a PDF to begin.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(5, 0))
        
    def update_engine_info(self):
        """Update the engine info label with details about the selected engine"""
        engine = self.selected_engine.get()
        info = {
            OCREngine.TESSERACT: "Fast, accurate, 100+ languages",
            OCREngine.EASYOCR: "Deep learning, good for complex layouts",
            OCREngine.WINDOWS_OCR: "Built-in Windows 10/11, fast"
        }
        self.engine_info.config(text=info.get(engine, ""))
        
    def open_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                if self.pdf_document:
                    self.pdf_document.close()
                self.pdf_document = fitz.open(file_path)
                self.total_pages = len(self.pdf_document)
                self.current_page = 0
                self.zoom_level = 1.0
                self.update_zoom_label()
                self.display_page()
                self.status_var.set(f"Loaded: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open PDF: {str(e)}")
                
    def display_page(self):
        if not self.pdf_document:
            return
            
        page = self.pdf_document[self.current_page]
        
        # Render page to image with zoom
        matrix = fitz.Matrix(self.zoom_level * 1.5, self.zoom_level * 1.5)
        pix = page.get_pixmap(matrix=matrix)
        
        # Convert to PIL Image
        img_data = pix.tobytes("ppm")
        self.current_image = Image.open(io.BytesIO(img_data))
        
        # Convert to PhotoImage for display
        self.photo_image = ImageTk.PhotoImage(self.current_image)
        
        # Update canvas
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image, tags="pdf")
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Update page label
        self.page_label.config(text=f"Page: {self.current_page + 1} / {self.total_pages}")
        
        # Clear selection
        self.selection_rect = None
        self.selection_start = None
        
    def prev_page(self):
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            self.display_page()
            
    def next_page(self):
        if self.pdf_document and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.display_page()
            
    def zoom_in(self):
        self.zoom_level = min(3.0, self.zoom_level + 0.25)
        self.update_zoom_label()
        self.display_page()
        
    def zoom_out(self):
        self.zoom_level = max(0.25, self.zoom_level - 0.25)
        self.update_zoom_label()
        self.display_page()
        
    def update_zoom_label(self):
        self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
        
    def on_mouse_press(self, event):
        if not self.current_image:
            return
        # Get canvas coordinates accounting for scroll
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.selection_start = (x, y)
        
        # Remove existing selection rectangle
        self.canvas.delete("selection")
        
    def on_mouse_drag(self, event):
        if not self.selection_start:
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Draw selection rectangle
        self.canvas.delete("selection")
        self.canvas.create_rectangle(
            self.selection_start[0], self.selection_start[1],
            x, y,
            outline="red", width=2, tags="selection"
        )
        
    def on_mouse_release(self, event):
        if not self.selection_start:
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Store selection coordinates
        x1, y1 = self.selection_start
        x2, y2 = x, y
        
        # Normalize coordinates (ensure x1 < x2, y1 < y2)
        self.selection_rect = (
            min(x1, x2), min(y1, y2),
            max(x1, x2), max(y1, y2)
        )
        
        self.status_var.set(f"Selection: ({int(self.selection_rect[0])}, {int(self.selection_rect[1])}) to ({int(self.selection_rect[2])}, {int(self.selection_rect[3])})")
        
    def clear_selection(self):
        self.canvas.delete("selection")
        self.selection_rect = None
        self.selection_start = None
        self.status_var.set("Selection cleared.")
        
    def ocr_current_page(self):
        if not self.current_image:
            messagebox.showwarning("Warning", "Please open a PDF first.")
            return
            
        engine = self.selected_engine.get()
        self.status_var.set(f"Performing OCR on current page using {engine}...")
        self.root.update()
        
        def do_ocr():
            try:
                text = OCREngine.perform_ocr(self.current_image, engine)
                self.root.after(0, lambda: self.display_ocr_result(text, f"Page {self.current_page + 1} ({engine})"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("OCR Error", str(e)))
                self.root.after(0, lambda: self.status_var.set("OCR failed."))
                
        threading.Thread(target=do_ocr, daemon=True).start()
        
    def ocr_selection(self):
        if not self.current_image:
            messagebox.showwarning("Warning", "Please open a PDF first.")
            return
            
        if not self.selection_rect:
            messagebox.showwarning("Warning", "Please make a selection first.\nClick and drag on the PDF to select an area.")
            return
            
        engine = self.selected_engine.get()
        self.status_var.set(f"Performing OCR on selection using {engine}...")
        self.root.update()
        
        def do_ocr():
            try:
                # Crop the image to selection
                x1, y1, x2, y2 = self.selection_rect
                cropped = self.current_image.crop((int(x1), int(y1), int(x2), int(y2)))
                text = OCREngine.perform_ocr(cropped, engine)
                self.root.after(0, lambda: self.display_ocr_result(text, f"Selection ({engine})"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("OCR Error", str(e)))
                self.root.after(0, lambda: self.status_var.set("OCR failed."))
                
        threading.Thread(target=do_ocr, daemon=True).start()
        
    def ocr_entire_document(self):
        if not self.pdf_document:
            messagebox.showwarning("Warning", "Please open a PDF first.")
            return
            
        engine = self.selected_engine.get()
        self.status_var.set(f"Performing OCR on entire document using {engine}...")
        self.root.update()
        
        def do_ocr():
            try:
                all_text = []
                for page_num in range(self.total_pages):
                    self.root.after(0, lambda p=page_num: self.status_var.set(f"Processing page {p + 1} of {self.total_pages} using {engine}..."))
                    
                    page = self.pdf_document[page_num]
                    matrix = fitz.Matrix(1.5, 1.5)
                    pix = page.get_pixmap(matrix=matrix)
                    
                    img_data = pix.tobytes("ppm")
                    img = Image.open(io.BytesIO(img_data))
                    
                    text = OCREngine.perform_ocr(img, engine)
                    all_text.append(f"--- Page {page_num + 1} ---\n{text}\n")
                    
                full_text = "\n".join(all_text)
                self.root.after(0, lambda: self.display_ocr_result(full_text, f"Entire Document ({engine})"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("OCR Error", str(e)))
                self.root.after(0, lambda: self.status_var.set("OCR failed."))
                
        threading.Thread(target=do_ocr, daemon=True).start()
        
    def display_ocr_result(self, text, source):
        self.text_output.delete(1.0, tk.END)
        self.text_output.insert(tk.END, text)
        self.status_var.set(f"OCR complete: {source}")
        
    def save_text(self):
        text = self.text_output.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "No text to save.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save OCR Text",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text)
                self.status_var.set(f"Saved to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")


def main():
    root = tk.Tk()
    app = PDFOCRApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
