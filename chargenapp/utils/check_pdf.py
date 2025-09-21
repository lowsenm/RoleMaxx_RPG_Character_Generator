from pdfrw import PdfReader, PdfName

def list_pdf_fields(pdf_path):
    pdf = PdfReader(pdf_path)
    print("📄 Fields in PDF:")
    for page in pdf.pages:
        annotations = page.get(PdfName.Annots)
        if annotations:
            for annot in annotations:
                if annot.get(PdfName.T):
                    print(annot[PdfName.T].to_unicode())

list_pdf_fields("C:/Users/lowse/Documents/Games/CharGen/CharGen-2.0/charsheettemp.pdf")
