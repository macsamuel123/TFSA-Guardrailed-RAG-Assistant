from pydantic import BaseModel
from fastapi import FastAPI
from app.pipeline import orchestrate

app =FastAPI(title="TFSA Assistant")

class AskRequest(BaseModel):
    question :str

@app.post("/ask")
def ask(request: AskRequest):
    return {"result":orchestrate(request.question)}

@app.get("/health")
def health():
    return {"status":"ok"}