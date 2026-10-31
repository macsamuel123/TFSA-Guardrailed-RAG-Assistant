from app.pipeline import saved_chunks, matrix
from app.rag import retrieve
relevant = [
    "Can I withdraw money from my TFSA at any time?",
    "What happens if I contribute more than my TFSA limit?",
    "Can I carry forward unused TFSA contribution room?",
    "What happens to my TFSA when I die?",
    "Can I have more than one TFSA?",
    "How do I transfer money between two TFSAs?",
    "What investments are allowed in a TFSA?",
    "Can a non-resident contribute to a TFSA?",
]

finance_not_tfsa = [
    "How does a mortgage work?",
    "How is my credit score calculated?",
    "What is the difference between a stock and a bond?",
    "How do index funds work?",
    "How do I file my income taxes in Canada?",
]

off_topic = [
    "How do I bake bread?",
    "Who won the World Cup?",
    "What's the capital of France?",
    "How do I write a list comprehension in Python?",
]

def calibrate():
    groups = {
        "RELEVANT": relevant,
        "FINANCE, NOT TFSA": finance_not_tfsa,
        "OFF-TOPIC": off_topic,
    }
    for group_name, questions in groups.items():
        print(f"\n=== {group_name} ===")
        for q in questions:
            results = retrieve(q, saved_chunks, matrix)
            print(f"{results[0]['score']:.3f}  {q}")

if __name__ == "__main__":
    calibrate()

