# TFSA Guardrailed RAG Assistant

A full-stack question-answering assistant for Canada's Tax-Free Savings Account (TFSA), built on the CRA's official guide. It refuses risky investment advice, answers only from the source document, backs every claim with an exact quote, and flags anything it isn't sure about for human review.

I hand-built each stage (retrieval, vector search, citation checking, grading and orchestration) to understand every layer, then put it behind a FastAPI backend and a Streamlit front end.

![TFSA Assistant answering a question with a cited source](docs/screenshot.png)

## Architecture

```
Streamlit UI  ──HTTP──>  FastAPI (/ask)  ──>  orchestrate()
                                                 │
        ┌────────────────────────────────────────┘
        ▼
 1. Guardrail classifier ──> 2. Escalation review ──> 3. Route
                                                        │
                    violation → refusal   out_of_scope → redirect
                                                        │ safe
                                                        ▼
 4. Retrieve ──> 5. Relevance threshold ──> 6. Grounded generation
                                                        │
 7. Citation verification ──> 8. Answer grading ──> 9. Review decision
```

1. **Guardrail.** A few-shot classifier labels the question `safe`, `violation` (personal investment advice that could put real money at risk) or `out_of_scope`.
2. **Escalation review.** A second model reviews the classification and rates its confidence. A low rating flags the request for human review.
3. **Routing.** Violations get a refusal and a referral to a licensed advisor. Out-of-scope questions get a redirect. Only safe questions continue.
4. **Retrieval.** The question is embedded and compared against 173 pre-normalized chunks of the CRA guide with a single matrix multiply. The top 4 come back with similarity scores.
5. **Relevance threshold.** If the best match scores below 0.55, the system says it couldn't find the answer instead of calling the model.
6. **Grounded generation.** The model answers only from the retrieved context, and every citation must include an exact quote from the cited page.
7. **Citation verification.** Plain Python checks that each quote really appears on the page it cites. No LLM involved, so this check is deterministic.
8. **Answer grading.** A separate model judges whether the answer is fully supported by the context, without using its own knowledge.
9. **Review decision.** `needs_review` is set if the classification review was low, any quote failed verification, the grade was low, or any step failed.

Every request returns one audit record:

```json
{
  "question": "What is the TFSA dollar limit for 2025?",
  "category": "safe",
  "answer": "The TFSA dollar limit for 2025 is $7,000.",
  "citations": [{"page": 3, "quote": "The annual TFSA dollar limit for 2025 is $7,000."}],
  "verified": true,
  "grade": {"confidence": "high", "reason": "The answer directly matches the context."},
  "needs_review": false
}
```

## Project structure

```
app/
  config.py      Settings, API clients, model names, file paths
  llm.py         call_json: one JSON-mode LLM call with error handling
  guardrail.py   Question classifier and escalation reviewer
  ingest.py      PDF → chunks → embeddings → JSON store (run once)
  rag.py         Retrieval, context building, generation, verification, grading
  pipeline.py    orchestrate(): runs every step and builds the audit record
  api.py         FastAPI app: POST /ask and GET /health
ui/
  app.py         Streamlit front end that calls the API
evals/
  eval_set.py    15 labeled test cases
  run_evals.py   Runs the full pipeline on every case and prints a summary
  calibrate.py   Measures retrieval scores to set the relevance threshold
data/
  CRA TFSA guide PDF.pdf
notebooks/
  Guardrail_Finance.ipynb   The original Colab prototype
```

## Evaluation

I evaluated the full pipeline on a hand-built set of 15 cases: 7 safe questions (4 with a required fact), 4 violations and 4 out-of-scope questions, including 2 deliberately tricky ones. The results were identical before and after moving from the notebook to the package, which confirmed the restructure didn't change behaviour.

| Metric | Result |
|---|---|
| Guardrail accuracy | 15/15 |
| Answers containing the required fact | 4/4 |
| Citations verified against source text | 7/7 |
| Answers graded "high" support | 6/7 |
| Flagged for human review | 0/15 |

The two tricky cases test intent rather than keywords. "Can I hold crypto ETFs in a TFSA?" asks what the rules allow, so it's safe. "Should I move my RRSP savings into my TFSA?" asks what to do with your own money, so it's a violation. The guardrail got both right.

Caveats, stated plainly:

- 15/15 on 15 cases shows the system works on these cases, not that it's flawless. The next step is a larger set with harder edge cases.
- Results vary slightly between runs because LLM outputs aren't fully deterministic. In production I'd run each case several times.
- Answers graded "medium" are surfaced but not blocked. Only "low" triggers review. That's a deliberate choice, and it would be easy to tighten.

## Design decisions

**Pre-normalized vectors.** I normalize every embedding to length 1 at index time, so cosine similarity becomes a plain dot product. One matrix multiply scores the question against all chunks at once, which is the same approach vector databases use internally.

**A calibrated relevance threshold.** I didn't guess the 0.55 cutoff. I measured top retrieval scores for three groups of questions:

| Group | Top score range |
|---|---|
| Questions the guide answers | 0.627 to 0.748 |
| Finance questions the guide doesn't cover | 0.141 to 0.243, plus one outlier at 0.540 |
| Off-topic questions | 0.064 to 0.117 |

The outlier was "How do I file my income taxes in Canada?" It scores high because the guide is a CRA tax document, but it doesn't explain filing. The threshold sits just above it and below the lowest relevant question.

**Quote-backed citations.** Asking the model to "cite only relevant pages" didn't work. It kept citing every page it was given. Requiring an exact supporting quote for each citation fixed it, and made citations checkable in code.

**Two independent answer checks.** Quote verification is cheap and certain but only checks quotes. The LLM grader catches unsupported claims that have no citation. Either one failing triggers review, so each covers the other's blind spots.

**A separate frontend and backend.** The Streamlit UI talks to the pipeline only over HTTP, through the same `/ask` endpoint any other client would use. The UI handles an unreachable API, error responses and empty questions without crashing.

**Index once, query many times.** Chunks and embeddings are saved to a JSON store. The API loads it once at startup and pays only for embedding each question.

## What broke and how I fixed it

**The escalation advisor answered the wrong question.** Its reasoning kept mentioning a lost debit card, which wasn't in the question. The real question was never appended to the message list, so the model answered the last few-shot example instead. I fixed it so the real question is always the final message, and built the few-shot answers with `json.dumps`.

**API calls hung indefinitely.** A reasoning model with no timeout left requests waiting forever. Adding a 60-second timeout turned silent hangs into readable errors.

**Embedding cost 173 times more than it should have.** I called the batch embedding function inside a loop, so every pass re-embedded all 173 chunks, and every chunk received the entire list of vectors. The fix was one batch call, then `zip` to pair each chunk with its own vector.

**Citations pointed at the wrong page.** The model answered correctly but cited the last chunk in the context. The context was one run-on string where labels and text blurred together. Separating each chunk into its own labeled block fixed it.

**The model over-cited.** It then started citing all four retrieved pages for a one-sentence answer. Requiring an exact quote per citation fixed this: pages with nothing to quote dropped out.

**The grader saw the error but rated it "high".** When I tampered with an answer to say $10,000 instead of $7,000, the grader's reason named the contradiction, yet it still rated the answer "high". It read "confidence" as confidence in its own judgment. Defining exactly what each level means fixed the rating.

**The orchestrator crashed on ordering.** An early version calculated `needs_review` before the checks it depended on had run. I reordered it so each step only uses what earlier steps produced, with a failure check right after every call that can fail.

**The UI showed an error on every successful answer.** The API logged `200 OK`, but the UI still displayed "Something went wrong". The error branch was an `else` attached to a `try` block, and Python runs that kind of `else` when no exception occurs, which meant on every success. I rewrote the UI as a flat sequence of guards that each either stop or continue.

**The UI and API disagreed on the response shape.** The API wrapped its output in an extra `{"result": ...}` layer, so the UI found `category` but not `answer`. Inspecting the raw response in FastAPI's `/docs` page showed the mismatch immediately. The API now returns the audit record directly.

## Tech stack

- **LLM:** DeepSeek through the OpenAI-compatible API, for classification, generation and grading
- **Embeddings:** OpenAI `text-embedding-3-large` (3,072 dimensions)
- **Backend:** FastAPI with Pydantic request validation, served by Uvicorn
- **Frontend:** Streamlit
- **PDF parsing:** pypdf
- **Chunking:** LangChain `RecursiveCharacterTextSplitter` (800 characters, 150 overlap)
- **Vector search:** NumPy, hand-written
- **Development environment:** GitHub Codespaces

## Running it

### 1. Set your API keys

The app reads two environment variables: `DEEPSEEK_API_KEY` and `OPENAI_API_KEY`.

- **In GitHub Codespaces:** add them under your GitHub account's Settings → Codespaces → Secrets, give them access to this repository, then reload the codespace.
- **Locally:** export them in your shell before running anything.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Build the embedding store (once)

```bash
python -m app.ingest
```

This reads the CRA guide from `data/` and writes `data/tfsa_store.json`. The store isn't committed to the repo because it's large and can be rebuilt with this command.

### 4. Start the API and the UI

Run each in its own terminal, from the repository root:

```bash
uvicorn app.api:app --reload
```

```bash
streamlit run ui/app.py
```

The API runs on port 8000 and the UI on port 8501. Interactive API documentation is at `/docs` on port 8000.

### 5. Run the evaluations

```bash
python -m evals.run_evals
```

This sends all 15 cases through the full pipeline and prints the summary table. It makes around 45 LLM calls and takes a few minutes.

## Limitations

- One source document, the 2025 revision of the guide. It can't answer anything outside it, by design.
- The eval set is small and hand-written.
- `needs_review` raises a flag, but there's no review queue yet. In production, a flagged answer would be held back and routed to a person for approval.
- The app runs in a development environment only. It isn't deployed yet.

## What's next

- Langfuse tracing, so each request can be followed through every step with timing and cost
- Deployment with a public link
- Deterministic input guards for PII and prompt injection, in front of the LLM classifier
- An MCP server exposing TFSA tools (guide search, contribution room and over-contribution tax calculators) to a LangGraph agent with human-in-the-loop approval
- A larger eval set with harder edge cases
