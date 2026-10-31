import numpy as np
from app.config import embedding,SCORE_THRESHOLD
from app.llm import call_json
import re 
import json

OUTPUT_JSON = '{"answer": "one or two sentences", "citations": [{"page": 3, "quote": "short exact text from that page"}]}'

def retrieve(question,chunks,matrix,k=4):
  question_embedding=embedding.embed_query(question)
  question_array=np.array(question_embedding)
  question_length=np.linalg.norm(question_array)
  question_vector=question_array/question_length
  scores=np.dot(matrix,question_vector)
  indices=np.argsort(scores)[::-1][:k]
  return [{**chunks[i],"score": float(scores[i])} for i in indices]

def build_context(results):
  context_string=""
  for r in results:
    context_string += f"[Source: {r['source']}, page {r['page']}]\n{r['text']}\n\n"
  return context_string

def generate_answer(question, results):
  if results[0]["score"]<= SCORE_THRESHOLD:
    return {"answer": "I couldn't find this in the TFSA guide.", "citations": []}
 
  context_string = build_context(results)

  sys_prompt=f"""Answer using only the context provided by the user.
  Every citation must include a short exact quote from that page that directly supports the answer.
  If you cannot quote supporting text from a page, do not cite it.
  If the context does not contain the answer, say so plainly and return no citations.
  Do not give personal investment advice.
  Respond only in JSON: {OUTPUT_JSON}
  """
  messages = [
    {"role": "system", "content": sys_prompt},
    {"role": "user", "content": f"Context:\n{context_string}\n\nQuestion: {question}"},
  ]
  return call_json(messages)

def normalize(s):
    return re.sub(r"\s+", " ", s.lower().strip())

def verify_citations(answer, results):
  failed=[]
  for citation in answer["citations"]:
    found=False
    page=citation["page"]
    text=citation["quote"]
    for result in results:
      if normalize(text) in normalize(result["text"]) and result["page"]==page:
        found=True
        break
    if not found:
      failed.append(citation)
  return {"verified": len(failed) == 0, "failed": failed}


def grade_answer(question,results,answer):
  sys_prompt="""Review an answer generated from retrieved context. Judge only
  whether the answer is fully supported by the context and actually answers the
  question. Do not use your own knowledge. If any claim in the answer cannot be
  verified from the context, rate it low. Rate how well the answer is supported by the context:
  “high”: every claim is directly supported by the context,
  “medium”: the answer is partly supported or incomplete,
   or “low”: any claim is unsupported by or contradicts the context.
  Low means a human should review it. Respond only in JSON:
   {"confidence": "...", "reason": "..."}
  """
  messages=[{"role":"system","content":sys_prompt},
            {"role":"user","content":"Context:"+build_context(results)+"\nQuestion:"+question+"\nAnswer:"+json.dumps(answer)}]
  return call_json(messages)

