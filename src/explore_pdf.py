import pdfplumber

PDF_PATH = "data/raw/26-27_GP_GrandPrixDeFrance_M_SP.pdf"

with pdfplumber.open(PDF_PATH) as pdf:
    print("Number of pages:", len(pdf.pages))
    first_page = pdf.pages[0]
    print(first_page.extract_text())