from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import concurrent
import PyPDF2
import pandas as pd
import base64
import os


client = OpenAI(api_key=os.environ.get("deepseek_api_key"), base_url=os.environ.get("deepseek_base_url"))

dir_pdfs = './pdfs'
pdf_files = [os.path.join(dir_pdfs, f) for f in os.listdir(dir_pdfs) if f.endswith('.pdf')]

# def upload_single_pdf(file_path: str, vector_store_id: str):
#     file_name = os.path.basename(file_path)
#     try:
#         file_response = client.files.create(file=open(file_path, 'rb'), purpose='assistant')
#         attach_response = client.vector_stores.files.create(
#             vector_store_id=vector_store_id,
#             file_id=file_response.id
#         )
#         return {"file": file_name, "status": "success"}
#     except Exception as e:
#         print((f"Error with {file_name}: {str(e)}"))
#         return {"file": file_name, "status": "failed", "error": str(e)}
    
# def upload_pdf_files_to_vector_store(vector_store_id: str):
#     pdf_files = [os.path.join(dir_pdfs, f) for f in os.listdir(dir_pdfs)]
#     stats = {"total_files": len(pdf_files), "successful_uploads": 0, "errors": []}

#     print(f"{len(pdf_files)} PDF files to process. Uploading in parallel...")

#     with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
#         futures = {executor.submit(upload_single_pdf, file_path, vector_store_id): file_path for file_path in pdf_files}
#         for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
#             result = future.result()
#             if result["status"] == "success":
#                 stats["successful_uploads"] += 1
#             else:
#                 stats["failed_uploads"] += 1
#                 stats["errors"].append(result)

#     return stats

# def create_vector_store(store_name: str) -> dict:
#     try:
#         vector_store = client.vector_stores.create(name=store_name)
#         details = {
#             "id": vector_store.id,
#             "name": vector_store.name,
#             "created_at": vector_store.created_at,
#             "file_count": vector_store.file_counts.completed,
#         }
#         print("Vector store created:", details)
#         return details
#     except Exception as e:
#         print("Error creating vector store:", str(e))
#         return {}
    
# store_name = "my_vector_store"
# vector_store_datails = create_vector_store(store_name)
# upload_pdf_files_to_vector_store(vector_store_datails["id"])


def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text

def generate_questions(pdf_path):
    text = extract_text_from_pdf(pdf_path)

    prompt = (
        "Can you generate a question that can only be answered from this document?:\n"
        f"{text}\n\n"
    )

    response = client.chat.completions.create(
        model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are an assistant that creates questions based on document content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4096,
    )

    question = response.choices[0].message.content
    print(f"Generated question: {question}")

    return question

generate_questions(pdf_files[0])