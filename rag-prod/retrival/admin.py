from django.contrib import admin
from .models import UploadedPDF, Query

@admin.register(UploadedPDF)
class UploadedPDFAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'file', 'upload_at')
    search_fields = ('name',)

@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ('id', 'pdf', 'user_query', 'created_at')
    search_fields = ('user_query', 'response')
    list_filter = ('created_at', 'pdf')
