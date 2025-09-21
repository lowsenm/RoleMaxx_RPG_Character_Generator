from pdfrw import PdfReader, PdfWriter, PdfName


def fillpdf(input_pdf_path, output_pdf_path, data_dict):
    template_pdf = PdfReader(input_pdf_path)

    ANNOT_KEY = PdfName.Annots
    ANNOT_FIELD_KEY = PdfName.T
    ANNOT_VAL_KEY = PdfName.V
    SUBTYPE_KEY = PdfName.Subtype
    WIDGET_SUBTYPE_KEY = PdfName.Widget

    for page in template_pdf.pages:
        annotations = page.get(ANNOT_KEY)
        if annotations:
            for annotation in annotations:
                if annotation.get(SUBTYPE_KEY) == WIDGET_SUBTYPE_KEY and annotation.get(ANNOT_FIELD_KEY):
                    key = annotation[ANNOT_FIELD_KEY].to_unicode()
                    if key in data_dict:
                        annotation.update(
                            {
                                ANNOT_VAL_KEY: data_dict[key]
                            }
                        )

    PdfWriter().write(output_pdf_path, template_pdf)

level = 3

character_data = {
    "Race": "Hairy",
    "Class": "High",
    "Background": "Low",
    "Level": str(level),
    "LevelTitle": "Grandee",
    "PersonalityTraits": "Hoarse, Roasted, Life",
    "Alignment": 'cra-cra',
    "OtherProficiencies&Languages": "Yayaya",
    "CharacterName": "Florbrid",
    "PlayerName": "Ben",
    "Backstory": "Yorgont was a terrible hotspur",
}

fillpdf("C:/Users/lowse/Documents/Games/CharGen/CharGen-2.0/charsheettemp.pdf", "C:/Users/lowse/Documents/Games/CharGen/CharGen-2.0/testcharsheet.pdf", character_data)
