from app.llm import call_json
import json 

examples_scenarios=[{"question":"Give me 5 stocks that will make me rich this year","category":"violation","reason":"Requests specific stock picks framed as guaranteed high returns"},
     {"question":"My friend told me to put my life savings into a meme coin, is that a good idea?","category":"violation","reason":"Seeks validation for high-risk, high-stakes investment advice"},
      {"question":"Can you explain what a P/E ratio means?","category":"safe","reason":"General financial education, not specific investment advice"},
    {"question":"What stock will 5x next week so I can invest in it?","category":"violation","reason":"Asks for a specific stock prediction promising extreme returns"},
     {"question":"Can I withdraw from my TFSA any time?","category":"safe","reason":"General account rules question, no risky action requested"},
      {"question":"What are the best performing tech stocks?","category":"safe","reason":"General market information, not a personal recommendation"},
      {"question":"What's the capital of France?","category":"out_of_scope","reason":"Unrelated to financial advice or risk"},
       {"question":"What's a good recipe for a quick weeknight dinner?","category":"out_of_scope","reason":"Unrelated to financial advice or risk"}]

GUARDRAIL_SYS = """You are a compliance classifier for a banking assistant.
Classify the user's question into exactly one category:
- "violation": asks for advice that could make the user risk real money
- "safe": finance-related and safe to answer (education, rules, general info)
- "out_of_scope": not related to finance
Respond only in JSON: {"category": "...", "reason": "..."}"""


def build_few_shots(examples):
    shots = []
    for ex in examples:
        shots.append({"role": "user", "content": ex["question"]})
        shots.append({"role": "assistant", "content": json.dumps(
            {"category": ex["category"], "reason": ex["reason"]})})
    return shots


def check_financial_advice(question):
  messages = [{"role": "system", "content": GUARDRAIL_SYS}]
  messages+=build_few_shots(examples_scenarios)
  usr_prompt={"role":"user","content": question}
  messages.append(usr_prompt)
  return call_json(messages)


ESCALATION_SYS = """You review a compliance classifier's decision.
Rate your confidence that the classification is correct: "high", "medium" or "low".
Low means a human should review it.
Respond only in JSON: {"confidence": "...", "reason": "..."}"""

def escalation_advisor(question, result):
  if not result or "category" not in result:
    return {"confidence":"low","reason": "Classifier returned no valid result"}
  messages = [  {"role": "system", "content": ESCALATION_SYS},
                {"role": "user", "content": f"Question: How much Tesla stock should I buy?\nClassification: {json.dumps({'category': 'safe', 'reason': 'Asking about Tesla stock'})}"},
                {"role": "assistant", "content": json.dumps({"confidence": "low", "reason": "Asks for a specific buy amount, which is personal investment advice. Likely a violation."})},
                {"role": "user", "content": f"Question: What's the capital of France?\nClassification: {json.dumps({'category': 'out_of_scope', 'reason': 'Unrelated to finance'})}"},
                {"role": "assistant", "content": json.dumps({"confidence": "high", "reason": "Clearly not a finance question."})},
                {"role": "user", "content": f"Question: {question}\nClassification: {json.dumps(result)}"},
            ]

  return call_json(messages)