from app.config import STORE_PATH
from app.ingest import load_store, build_matrix
from app.guardrail import check_financial_advice, escalation_advisor
from app.rag import retrieve, generate_answer, verify_citations, grade_answer

#Formats the output from the LLM into a JSON format
def make_result(question, category=None, answer=None, citations=None,
                verified=None, grade=None, needs_review=False):
    return {"question": question, "category": category, "answer": answer,
            "citations": citations or [], "verified": verified,
            "grade": grade, "needs_review": needs_review}


saved_chunks = load_store(STORE_PATH)
matrix = build_matrix(saved_chunks)

def orchestrate(question):
    # 1. Guardrail, and stop immediately if it failed
    classification = check_financial_advice(question)
    if classification is None:
        return make_result(question, answer="Something went wrong. Please try again.",
                           needs_review=True)

    # 2. Review the classification
    review = escalation_advisor(question, classification)
    category = classification["category"]
    review_low = review is None or review["confidence"] == "low"

    # 3. Route
    if category == "violation":
        return make_result(question, category=category,
                           answer="I can't give personal investment advice. Consider speaking with a licensed financial advisor.",
                           needs_review=review_low)
    if category == "out_of_scope":
        return make_result(question, category=category,
                           answer="I can only answer questions about TFSAs.",
                           needs_review=review_low)

    # 4. Safe: run the answer pipeline
    results = retrieve(question, saved_chunks, matrix)
    answer = generate_answer(question, results)
    if answer is None:
        return make_result(question, category=category,
                           answer="Something went wrong. Please try again.",
                           needs_review=True)
    verification = verify_citations(answer, results)
    grade = grade_answer(question, results, answer)

    # 5. NOW decide on review, after every check has run
    needs_review = (review_low
                    or grade is None
                    or not verification["verified"]
                    or grade["confidence"] == "low")

    return make_result(question, category=category,
                       answer=answer["answer"], citations=answer["citations"],
                       verified=verification["verified"], grade=grade,
                       needs_review=needs_review)
