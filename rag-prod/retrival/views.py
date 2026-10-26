from django.conf import settings
import os
from django.shortcuts import render, redirect
from django.http import HttpResponse
from dotenv import load_dotenv

from .forms import PDFUploadForm
from .models import UploadedPDF, Query

try:
    from pypdf import PdfReader
except (ImportError, ModuleNotFoundError):
    from PyPDF2 import PdfReader

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except (ImportError, ModuleNotFoundError):
    from langchain.text_splitter import RecursiveCharacterTextSplitter

try:
    from langchain_core.documents import Document
except (ImportError, ModuleNotFoundError):
    from langchain.schema import Document

from langchain_groq import ChatGroq
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

try:
    from langchain_qdrant import QdrantVectorStore
except (ImportError, ModuleNotFoundError):
    from langchain_community.vectorstores import Qdrant as QdrantVectorStore

from qdrant_client import QdrantClient

try:
    from langchain_classic.chains import RetrievalQA
except (ImportError, ModuleNotFoundError):
    try:
        from langchain.chains import RetrievalQA
    except (ImportError, ModuleNotFoundError):
        from langchain.chains.retrieval_qa.base import RetrievalQA

try:
    from langchain_core.prompts import PromptTemplate
except (ImportError, ModuleNotFoundError):
    from langchain.prompts import PromptTemplate
from  langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

def get_google_model(model="gemini-3.5-flash"):
    key = (os.getenv("GOOGLE_API_KEY") or getattr(settings, "GOOGLE_API_KEY", "") or "").strip().strip('"').strip("'")
    if not key:
        return None
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=0.1,
        max_retries=2,
        google_api_key=key,
    )
    
# groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_APIA_KEY")
# google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

# llm = ChatGroq(temperature=0.1, groq_api_key=groq_api_key, model_name="llama-3.1-8b-instant") if groq_api_key else None


# Alias for compatibility
get_openai_model = get_google_model

google_api_key = (os.getenv("GOOGLE_API_KEY") or getattr(settings, "GOOGLE_API_KEY", "") or "").strip().strip('"').strip("'")
groq_api_key = google_api_key  # Retained for backwards compatibility with utils

llm = get_google_model()
vector_search = None



def home(request):
    pdf_id = request.session.get('pdf_id')
    uploaded_pdf = UploadedPDF.objects.filter(id=pdf_id).first() if pdf_id else None
    has_collection = bool(vector_search or request.session.get('qdrant_collection'))
    recent_queries = Query.objects.order_by('-created_at')[:5]
    return render(request, "home.html", {
        "has_collection": has_collection,
        "uploaded_pdf": uploaded_pdf,
        "recent_queries": recent_queries,
    })


def redirect_to_upload(request):
    return redirect("upload_pdf")


def get_vector_store(request):
    global vector_search
    collection_name = request.session.get('qdrant_collection')
    qdrant_url = request.session.get('qdrant_url') or os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if vector_search is not None and getattr(vector_search, 'collection_name', None) == collection_name:
        return vector_search

    if collection_name and qdrant_url:
        try:
            embeddings = FastEmbedEmbeddings()
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
            vector_search = QdrantVectorStore(
                client=client,
                collection_name=collection_name,
                embedding=embeddings,
                validate_collection_config=False,
            )
            return vector_search
        except Exception as e:
            print(f"Error reconnecting to Qdrant: {e}")
    return None


def ask_question(request):
    vector_store = get_vector_store(request)
    has_collection = vector_store is not None
    answer = None
    question = ""
    source_docs = []
    error = None

    # Retrieve current active UploadedPDF model instance
    pdf_id = request.session.get('pdf_id')
    uploaded_pdf = None
    if pdf_id:
        uploaded_pdf = UploadedPDF.objects.filter(id=pdf_id).first()
    if not uploaded_pdf:
        uploaded_pdf = UploadedPDF.objects.order_by('-id').first()

    if request.method == "POST":
        question = request.POST.get("question", "").strip()
        if not question:
            error = "Please enter a question."
        elif not vector_store:
            error = "No document indexed in vector storage. Please upload a PDF first."
        else:
            try:
                prompt_template = """Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context:
{context}

Question: {question}

Helpful Answer:"""
                QA_PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

                global llm
                load_dotenv(override=True)
                current_google_key = (os.getenv("GOOGLE_API_KEY") or getattr(settings, "GOOGLE_API_KEY", "") or "").strip().strip('"').strip("'")

                if current_google_key:
                    llm = ChatGoogleGenerativeAI(
                        model="gemini-3.5-flash",
                        temperature=0.1,
                        max_retries=2,
                        google_api_key=current_google_key,
                    )
                else:
                    llm = None

                if llm:
                    try:
                        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
                        qa_chain = RetrievalQA.from_chain_type(
                            llm=llm,
                            chain_type="stuff",
                            retriever=retriever,
                            return_source_documents=True,
                            chain_type_kwargs={"prompt": QA_PROMPT}
                        )
                        result = qa_chain.invoke({"query": question})
                        answer = result.get("result")
                        source_docs = result.get("source_documents", [])
                    except Exception as llm_err:
                        docs = vector_store.similarity_search(question, k=3)
                        source_docs = docs
                        answer = (
                            f"LLM API Authentication / Execution Error: {llm_err}.\n\n"
                            "Please verify your GOOGLE_API_KEY at https://aistudio.google.com/app/apikey.\n\n"
                            "Here are the relevant excerpts directly retrieved from your document via Qdrant:"
                        )
                else:
                    docs = vector_store.similarity_search(question, k=3)
                    source_docs = docs
                    error_reason = "Google API Key is not configured yet. Please set GOOGLE_API_KEY in your .env file."

                    answer = (
                        f"Notice: {error_reason}\n\n"
                        "Here are the most relevant excerpts retrieved from your document via Qdrant & FastEmbed:"
                    )

                # Persist the query and generated response to the Query model
                if uploaded_pdf and answer:
                    Query.objects.create(
                        pdf=uploaded_pdf,
                        user_query=question,
                        response=answer
                    )

            except Exception as e:
                error = f"Error generating answer: {str(e)}"

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            from django.http import JsonResponse
            return JsonResponse({
                "question": question,
                "answer": answer,
                "error": error,
                "sources": [doc.page_content for doc in source_docs] if source_docs else []
            })

    # Retrieve recent queries for this PDF or general history
    recent_queries = []
    if uploaded_pdf:
        recent_queries = uploaded_pdf.queries.order_by('-created_at')[:10]
    else:
        recent_queries = Query.objects.order_by('-created_at')[:10]

    return render(request, "ask_question.html", {
        "question": question,
        "answer": answer,
        "source_docs": source_docs,
        "error": error,
        "has_collection": has_collection,
        "uploaded_pdf": uploaded_pdf,
        "recent_queries": recent_queries,
    })


def upload_pdf(request):
    global vector_search
    if request.method == "POST":
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['pdf_file']
            documents = []
            
            try:
                # 1. Save uploaded file to UploadedPDF model
                uploaded_pdf = UploadedPDF.objects.create(
                    file=uploaded_file,
                    name=uploaded_file.name
                )

                # 2. Load and process the PDF
                uploaded_file.seek(0)
                pdf_reader = PdfReader(uploaded_file)
                for page_idx, page in enumerate(pdf_reader.pages, start=1):
                    text = page.extract_text()
                    if text:
                        doc = Document(
                            page_content=text,
                            metadata={"page": page_idx, "source": uploaded_file.name, "pdf_id": uploaded_pdf.id}
                        )
                        documents.append(doc)
                    
                if not documents:
                    return render(request, 'upload.html', {"form": form, "error": "Some pages couldn't be extracted from the PDF or no text found."})

                # 3. Split the text into chunks
                text_splitter = RecursiveCharacterTextSplitter(
                    separators=["\n\n", "-", "\n", " ", ".", ",", "\u200b", "\uff0c", "\u3001", "\u3002", "\uff0e", ""],
                    chunk_size=1000,
                    chunk_overlap=100,
                )
                texts = text_splitter.split_documents(documents)
                print("completed_text_splitting")
                
                # 4. Generate embeddings
                embeddings = FastEmbedEmbeddings()
                print("embeddings_stored")
                
                # 5. Store embeddings in Qdrant with QdrantVectorStore
                qdrant_api_key = os.getenv("QDRANT_API_KEY")
                qdrant_url = os.getenv("QDRANT_URL")
                collection_name = f"pdf_collection_{uploaded_pdf.id}"

                vector_search = QdrantVectorStore.from_documents(
                    texts,
                    embeddings,
                    url=qdrant_url,
                    api_key=qdrant_api_key,
                    collection_name=collection_name,
                    force_recreate=True
                )
                print("completed_vector_search")

                # 6. Store session state
                request.session['qdrant_collection'] = collection_name
                request.session['qdrant_url'] = qdrant_url
                request.session['pdf_id'] = uploaded_pdf.id
                request.session['pdf_name'] = uploaded_pdf.name
                request.session.modified = True
                return redirect('ask_question')
            
            except Exception as e:
                import traceback
                traceback.print_exc()
                return render(request, 'upload.html', {"form": form, "error": str(e)})
            
    else:
        form = PDFUploadForm()
    return render(request, "upload.html", {"form": form})