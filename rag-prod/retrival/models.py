from django.db import models

# Create your models here.

class UploadedPDF(models.Model):
    
    """ modul"""
    file=models.FileField(upload_to="uploads/", help_text="PDF file uploaded by the users")
    
    upload_at = models.DateField(auto_now_add=True, help_text="Timestamp when file is uploaded")
    name=models.CharField(max_length=255, blank=True, null=True, help_text = "Name of uploaded PDF")
    
    def __str__(self):
        return self.name if self.name else f"PDF uploaded at {self.upload_at}"
    

class Query(models.Model):
    """Model to store user Queries and requests"""
    user_query = models.TextField(help_text="the query asked by the user")
    response = models.TextField(help_text="The response provided by the system", blank =True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text="timestamp when query was made")
    
    pdf = models.ForeignKey(UploadedPDF, on_delete=models.CASCADE, related_name="queries", help_text="PDF related to this Query ")
    
    def __str__(self):
        pdf_title = self.pdf.name if (self.pdf and self.pdf.name) else "PDF"
        return f"Query on {pdf_title} at {self.created_at}"