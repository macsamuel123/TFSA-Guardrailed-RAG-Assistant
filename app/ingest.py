from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np
import re
import pypdf
import json

def load_document(file_path):
  pages=[]
  with open(file_path, 'rb') as file:
    pdf_reader = pypdf.PdfReader(file)
    for page_num,page in enumerate(pdf_reader.pages, start=1):
        raw = page.extract_text() or ""
        cleaned = re.sub(r"\s+", " ", raw).strip()
        if not cleaned:
            continue
        pages.append({"text": cleaned,"page": page_num,"source": os.path.basename(file_path)})
    return pages

def chunk_pages(pages, chunk_size=800,overlap=150):
  chunks=[]
  splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
  for page in pages:
    for i,piece in enumerate(splitter.split_text(page["text"])):
      chunks.append({"text":piece,"page":page["page"],"source":page["source"], "chunk_id": f"{page['source']}-p{page['page']}-c{i}"})
  return chunks

def embed_chunks(chunks):
  chunk_texts=[chunk["text"] for chunk in chunks]
  embeddings = embedding.embed_documents(chunk_texts)
  for chunk, vector in zip(chunks, embeddings):
    chunk["embedding"] = vector
  return chunks


def save_store(chunks,path):
  with open(path,'w') as f:
    json.dump(chunks,f)

def load_store(path):
  with open(path,'r') as f:
    return json.load(f)

def build_matrix(chunks):
  embeddings_array = np.array([chunk["embedding"] for chunk in chunks])
  lengths=np.linalg.norm(embeddings_array, axis=1, keepdims=True)
  matrix= embeddings_array/lengths
  return matrix
