import json
from app.rag import normalize, retrieve
from app.pipeline import orchestrate
from evals.eval_set import eval_set

def run_eval(eval_set):
    results = []
    for ex in eval_set:
        result = orchestrate(ex["question"])
        result["expected"] = ex["expected"]
        result["category_pass"] = result["category"] == ex["expected"]
        if ex.get("must_contain"):
          result["answer_pass"] = normalize(ex["must_contain"]) in normalize(result["answer"])
        else:
          result["answer_pass"] = None
        results.append(result)
    return results

def summarize(results):
  total = len(results)
  cat_passed = sum(1 for r in results if r["category_pass"])
  print(f"Guardrail accuracy: {cat_passed}/{total}")
  answer_tested = sum(1 for r in results if r["answer_pass"] is not None)
  answer_passed = sum(1 for r in results if r["answer_pass"] is True)
  print(f"Answer accuracy: {answer_passed}/{answer_tested}")
  grade_passed = sum(1 for r in results if r["grade"] and r["grade"]["confidence"] == "high")
  grade_tested = sum(1 for r in results if r["grade"] is not None)
  print(f"Graded high: {grade_passed}/{grade_tested}")
  verified_passed = sum(1 for r in results if r["verified"])
  verified_tested = sum(1 for r in results if r["verified"] is not None)
  print(f"Verification accuracy: {verified_passed}/{verified_tested}")
  flagged = sum(1 for r in results if r["needs_review"])
  print(f"Flagged: {flagged}/{total}")
  failures = [r for r in results
            if not r["category_pass"] or r["answer_pass"] is False]
  if not failures:
      print("No failures.")
  for r in failures:
      print(json.dumps(r, indent=2))

if __name__ == "__main__":
    results = run_eval(eval_set)
    summarize(results)