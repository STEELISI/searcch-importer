
from io import StringIO
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

def pdf_file_to_text(pdf_file_path):
    pdftext = StringIO()
    with open(pdf_file_path,"rb") as f:
        parser = PDFParser(f)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr,pdftext,laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr,device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
    return pdftext.getvalue()
