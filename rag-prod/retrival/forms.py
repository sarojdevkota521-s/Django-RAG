from .forms import forms

class PDFUploadForm(forms.Form):
    pdf_file =forms.FileField(
        label="Upload PDF", required=True
    )