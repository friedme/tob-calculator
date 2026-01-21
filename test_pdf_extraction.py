import pdfplumber

pdf_path = input("Enter path to your IBKR PDF: ")

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        print(f"\n========== PAGE {page_num + 1} ==========")
        text = page.extract_text()
        print(text[:2000])  # First 2000 characters
        print("\n...")

input("Press Enter to close...")