import os
import json
import re
from groq import Groq

# ── Module-level client: fails loudly at startup, not silently mid-request ──
_groq_api_key = os.getenv("GROQ_API_KEY")

if not _groq_api_key:
    raise EnvironmentError(
        "[voice_llm_evaluator] GROQ_API_KEY is not set. "
        "Add it to your .env file or environment before starting the server."
    )

client = Groq(api_key=_groq_api_key, timeout=15)


# ────────────────────────────────────────────────────────────────────────────

def evaluate_voice_answer(
    question: str,
    transcript: str,
    speech_metrics: dict = None,
    round_type: str = "hr",
    *args
):
    speech_metrics = speech_metrics or {}
    print("VOICE LLM EVALUATOR: evaluate_voice_answer() called")

    if round_type.lower() == "technical":
        role = "You are a strict senior technical interviewer."
        focus = """
Evaluate:
- technical correctness
- explanation depth
- clarity of concept
- logical reasoning
"""
    else:
        role = "You are a strict HR interviewer evaluating behavioral answers."
        focus = """
Evaluate:
- communication quality
- clarity of explanation
- logical storytelling
- use of STAR structure
"""

    wpm        = speech_metrics.get("wpm", 0)
    fillers    = speech_metrics.get("fillers", 0)
    thinking   = speech_metrics.get("thinking_pauses", 0)
    hesitation = speech_metrics.get("hesitation_pauses", 0)
    fluency    = speech_metrics.get("fluency", 0)
    confidence = speech_metrics.get("confidence", 0)

    prompt = f"""
{role}

You are evaluating a candidate's spoken interview answer.

{focus}

QUESTION:
{question}

CANDIDATE ANSWER (transcript):
{transcript}

SPEECH DELIVERY METRICS:

Words Per Minute: {wpm}
Filler Words: {fillers}
Thinking Pauses: {thinking}
Hesitation Pauses: {hesitation}
Fluency Score: {fluency}/10
Confidence Score: {confidence}/10

You MUST reference these speaking metrics when giving feedback.
---------------------

STRICT SCORING RUBRIC:

Relevance:
0–2 → completely unrelated or incorrect
3–4 → weakly related
5–6 → partially answers the question
7–8 → mostly answers the question
9–10 → fully answers with clear context

Clarity:
0–2 → very confusing
3–4 → unclear explanation
5–6 → understandable but messy
7–8 → clear explanation
9–10 → extremely clear and concise

Structure:
0–2 → no structure
3–4 → very poor flow
5–6 → basic structure
7–8 → good logical flow
9–10 → excellent STAR or logical storytelling

IMPORTANT RULES:

- Do NOT give high scores unless the answer truly deserves it.
- If the answer is short, vague, or missing examples → score must be ≤6.
- If the answer lacks STAR or logical structure → structure must be ≤6.
- If explanation is weak → clarity must be ≤6.

---------------------

Return ONLY valid JSON in this format:

{{
  "relevance": number,
  "clarity": number,
  "structure": number,
  "overall_score": number,

  "speaking_feedback": {{
      "pace_comment": "comment about WPM",
      "fluency_comment": "comment about fluency",
      "confidence_comment": "comment about confidence"
  }},

  "strengths": [
    "specific interviewer-style strength",
    "another realistic strength"
  ],

  "improvements": [
    "specific improvement suggestion",
    "another improvement suggestion"
  ],

  "tip": "short practical advice for improving interview answers"
}}
IMPORTANT:
- Do NOT include explanations outside JSON.
- Be honest and realistic like a real interviewer.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    raw = response.choices[0].message.content

    try:
        match = re.search(r"\{.*\}", raw, re.S)
        if match:
            raw = match.group()

        data = json.loads(raw)
        # Ensure speaking feedback always exists
        if not data.get("speaking_feedback"):
            if wpm < 90:
                pace_comment = f"The speaking pace was relatively slow at {wpm} words per minute."
            elif wpm > 130:
                pace_comment = f"The speaking pace was slightly fast at {wpm} words per minute."
            else:
                pace_comment = f"The speaking pace was within a comfortable range at {wpm} words per minute."

            if fillers > 4 or hesitation > 2:
                fluency_comment = f"Some hesitation was observed with {fillers} filler words and {hesitation} pauses."
            else:
                fluency_comment = "The response was delivered smoothly with minimal hesitation."

            if confidence >= 8:
                confidence_comment = f"The candidate spoke confidently with a confidence score of {confidence}/10."
            elif confidence >= 6:
                confidence_comment = f"The candidate showed moderate confidence with a confidence score of {confidence}/10."
            else:
                confidence_comment = f"The response showed some uncertainty, reflected in a confidence score of {confidence}/10."

            data["speaking_feedback"] = {
                "pace_comment": pace_comment,
                "fluency_comment": fluency_comment,
                "confidence_comment": confidence_comment
            }

        relevance  = float(data.get("relevance", 0))
        clarity    = float(data.get("clarity", 0))
        structure  = float(data.get("structure", 0))

        content_score = round((relevance + clarity + structure) / 3, 2)

        data["content_score"]  = content_score
        data["speech_metrics"] = speech_metrics
        return data

    except Exception as e:
        print("LLM PARSE ERROR:", e)
        pace_comment = f"The speaking pace was around {wpm} words per minute."
        fluency_comment = "The response was generally fluent."
        confidence_comment = f"The speaker showed a confidence level of {confidence}/10."

        return {
            "relevance": 4,
            "clarity": 4,
            "structure": 4,
            "overall_score": 4,
            "speaking_feedback": {
            "pace_comment": pace_comment,
            "fluency_comment": fluency_comment,
            "confidence_comment": confidence_comment
        },
            "strengths": [
                "The candidate attempted to answer the question",
                "Some ideas were understandable"
            ],
            "improvements": [
                "Provide clearer explanations",
                "Use structured storytelling such as STAR"
            ],
            "tip": "Use Situation → Task → Action → Result to structure behavioral answers"
        }