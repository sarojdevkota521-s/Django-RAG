from django.shortcuts import render
from django.shortcuts import render, redirect
from .forms import PDFUploadForm
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_groq import ChatGroq
from langchain_community.embeddings.fastembed import FastEmbedEnbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from langchain.chains import RetrievalQA
from langchain.promots import PromptTemplate
from django.http import HttpResponse
import os
import dotenv import load_dotenv
# Create your views here.



def home(request):
    return render(request, "qa_bot/home.html")

def redirect_to_upload(request):
    return render("upload")

load_dotenv()

groq_api_key = os.getenv("GROQ_APIA_KEY")
llm= ChatGroq(temperature=0.1, groq_api_key=groq_api_key, model_name="llama=3.1-8b-in")
vector_search =None


def upload_pdf(request):
    global vector_search
    if request.method == "POST":
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file =request.FILES['pdf_file']
            documents =[]
            
            try:
                # load and process the PDF
                pdf_reader =PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    text = page.extract-text()
                    if text:
                        doc = Document(page_content =text)
                        documents.append(doc)
                    else:
                        return HttpResponse({"error":"Some pages couldn't be extracted from the PDF."})
                    
                # split the text into chunks
                text_splitter = RecursiveCharacterTextSplitter(
                    seperators=["\n\n", "-", "\n"," ", ".", ",", "\u200b", "\uff0c", "\u3001", "\u3002", "\uff0e", ""],
                    chunk_size = 1000,
                    
                )
                        