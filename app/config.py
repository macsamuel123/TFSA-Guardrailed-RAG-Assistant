import os
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings

MODEL = "deepseek-v4-pro"
SCORE_THRESHOLD = 0.55
PDF_PATH="/workspaces/TFSA-Guardrailed-RAG-Assistant/data/CRA_TFSA-Guide.pdf"
STORE_PATH="/workspaces/TFSA-Guardrailed-RAG-Assistant/data/tfsa_store.json"
deepseek_api_key=os.getenv('DEEPSEEK_API_KEY')
if not deepseek_api_key:
    raise RuntimeError("DEEPSEEK_API_KEY is not set")

openai_api_key=os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise RuntimeError("DEEPSEEK_API_KEY is not set")

client= OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com",timeout=60)

embedding = OpenAIEmbeddings(
        model="text-embedding-3-large",
        openai_api_key=openai_api_key
    )

