import os
from PyPDF2 import PdfReader

def list_pdf_files(folder):
    return [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]

def choose_pdf_file(pdf_files):
    print("Available PDF files:")
    for i, f in enumerate(pdf_files, 1):
        print(f"{i}: {f}")
    while True:
        try:
            choice = int(input("Enter the number of the PDF to read: "))
            if 1 <= choice <= len(pdf_files):
                return pdf_files[choice - 1]
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a number.")

def list_pdf_fields(pdf_path):
    reader = PdfReader(pdf_path)
    fields = reader.get_fields()

    if not fields:
        print("No form fields found in this PDF.")
        return

    print(f"\nFields in '{pdf_path}':")
    for field_name, field in fields.items():
        value = field.get("/V", "")
        print(f"{field_name}: {value}")

if __name__ == "__main__":
    folder = os.getcwd()
    pdf_files = list_pdf_files(folder)
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
    else:
        selected_pdf = choose_pdf_file(pdf_files)
        list_pdf_fields(os.path.join(folder, selected_pdf))
