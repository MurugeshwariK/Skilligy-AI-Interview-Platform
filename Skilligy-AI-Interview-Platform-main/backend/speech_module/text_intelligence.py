import os, json, re
from groq import Groq

def analyze_text(answer, question):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""
You are a senior interview evaluator.

Question:
{question}

Candidate Answer:
{answer}

Score from 0 to 10 for:
- Relevance
- Clarity
- Structure
- Content quality

Return JSON only:

{{
  "relevance": number,
  "clarity": number,
  "structure": number,
  "content_quality": number
}}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}],
        temperature=0.1,
        max_tokens=300
    )

    raw = response.choices[0].message.content

    match = re.search(r"\{.*\}", raw, re.S)

    if not match:
        # fallback if LLM misbehaves
        return {
            "relevance": 5,
            "clarity": 5,
            "structure": 5,
            "content_quality": 5
        }

    try:
        return json.loads(match.group())
    except:
        return {
            "relevance": 5,
            "clarity": 5,
            "structure": 5,
            "content_quality": 5
        }
