from django.db import models

# Create your models here.

class UploadedPDF(models.Model):
    
    """ modul"""
    file=models.FileField(upload_to="uploads/", help_text="PDF file uploaded by the users")
    
    upload_at = models.DateField(auto_now_add=True, help_text="Timestamp when file is uploaded")
    name=models.CharField(max_length=255, blank=True, null=True, help_text = "Name of uploaded PDF")
    
    def __str__(self):
        return self.name if self.name else f"PDF uploaded at {self.uploaaded_at}"