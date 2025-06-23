import re
import PyPDF2

def extract_text_from_pdf(uploaded_file):
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        
        if len(reader.pages) == 0:
            return "Gagal membaca PDF: File kosong atau rusak."
        
        extracted_pages = []
        
        for page in reader.pages:
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    page_text = re.sub(r'[^\w\s.,!?;:()\-"\']', ' ', page_text)
                    page_text = re.sub(r'\s+', ' ', page_text)
                    extracted_pages.append(page_text.strip())
            except Exception:
                continue
        
        if not extracted_pages:
            return "Gagal membaca PDF: Tidak dapat mengekstrak teks."
        
        full_text = '\n\n'.join(extracted_pages)
        
        if len(full_text.strip()) < 50:
            return "Gagal membaca PDF: Teks terlalu pendek."
        
        return full_text
    
    except Exception as e:
        return f"Gagal membaca PDF: {str(e)}"