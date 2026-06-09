import os
import re
import json
from groq import Groq
# -------------------------------------------------
# Question history storage
# -------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

HISTORY_FILE = os.path.join(DATA_DIR, "question_history.json")

def load_history():
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump({}, f)
        return {}

    with open(HISTORY_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_history(history):

    os.makedirs(DATA_DIR, exist_ok=True)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

        f.flush()
        os.fsync(f.fileno())

    print("Question history saved to:", HISTORY_FILE)
    print("History content:", history)
# Groq Client
# -------------------------------------------------
def get_client():
    return Groq(
        api_key=os.getenv("GROQ_API_KEY"),
        timeout=15   # never block UI
    )

# -------------------------------------------------
# Safe call wrapper (prevents freezes)
# -------------------------------------------------
def safe_llm_call(func, fallback):
    try:
        return func()
    except Exception as e:
        print("LLM ERROR:", e)
        return fallback
# -------------------------------------------------
# QUESTION GENERATION
# -------------------------------------------------
def generate_questions(role: str, round_type: str):
    client = get_client()

    if round_type.lower() == "hr":
        prompt = """
        You are an experienced HR interviewer.

        Generate 12 completely DIFFERENT HR interview questions.

        Rules:

        - Each question must test a DIFFERENT competency.
        - Do NOT repeat similar situations.
        - Avoid repeating themes like conflict resolution multiple times.
        - Use diverse scenarios.

        Possible themes include:
        teamwork
        leadership
        adaptability
        handling failure
        time management
        decision making
        learning from mistakes
        communication challenges
        handling pressure
        career motivation
        initiative
        collaboration

        Return ONLY a numbered list of questions.
        """
       
    else:
        prompt = f"""
You are a technical interviewer.

Generate exactly 10 UNIQUE technical interview questions for the role: {role}.

Difficulty distribution:
- 6 easy
- 4 medium
- 2 slightly challenging

Rules:
- Focus on fundamentals
- Suitable for entry-level candidates
- Avoid system design questions
- Avoid repeating similar topics

Return ONLY a numbered list.
"""

    def call():
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content

    text = safe_llm_call(call, "")
    questions = []

    for line in text.split("\n"):
        q = line.strip("0123456789. ").strip()

        if not q:
            continue

        # skip LLM explanation lines
        if len(q) < 10:
            continue

        if "interview questions" in q.lower():
            continue

        questions.append(q)

    # -------------------------------------------------
    # HISTORY FILTERING (PREVENT REPEATS)
    # ------------------------------------------------
    history = load_history()
    key = f"{role.lower()}_{round_type.lower()}"

    previous = history.get(key, [])

    def normalize(text):
        return text.lower().replace("?", "").replace(".", "").strip()

    normalized_previous = [normalize(p) for p in previous]

    unique_questions = []

    for q in questions:
        nq = normalize(q)
        duplicate = False
        for prev in normalized_previous:
            if nq in prev or prev in nq:
                duplicate = True
                break

        if not duplicate:
            unique_questions.append(q)

    # If everything repeats, fallback to generated questions
    if not unique_questions:
        unique_questions = questions

    history[key] = previous + unique_questions

    save_history(history)

    return unique_questions[:5]
# -------------------------------------------------
# TEXT ANSWER EVALUATION
# -------------------------------------------------
def evaluate_answer(question: str, answer: str, round_type: str):
    client = get_client()

    if round_type.lower() == "hr":
        evaluation_prompt = f"""
You are a senior HR interviewer.

Question:
{question}

Candidate Answer:
{answer}

Evaluate fairly based on:
- Relevance to the question
- Clarity
- Realism of the example

Scoring:
0–3 = off topic
4–5 = weak
6–7 = acceptable
8–9 = strong
10 = excellent

Return JSON only:

{{
  "score": 0-10,
  "strengths": ["...", "..."],
  "areas_to_improve": ["...", "..."],
  "actionable_tip": "..."
}}
"""
    else:
        evaluation_prompt = f"""
You are a senior technical interviewer.

Question:
{question}

Candidate Answer:
{answer}

Evaluate based on:
- Correctness
- Coverage of key concepts
- Explanation quality

Scoring:
0–3 = wrong
4–5 = partially correct
6–7 = mostly correct
8–9 = strong
10 = excellent

Return JSON only:

{{
  "score": 0-10,
  "strengths": ["...", "..."],
  "areas_to_improve": ["...", "..."],
  "actionable_tip": "..."
}}
"""

    def call():
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": evaluation_prompt}],
            temperature=0.05,
            max_tokens=700
        )
        return response.choices[0].message.content

    raw = safe_llm_call(call, "")

    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        return {
            "score": 5,
            "strengths": ["Answered the question"],
            "areas_to_improve": ["More detail needed"],
            "actionable_tip": "Explain your answer more clearly."
        }

    try:
        result = json.loads(match.group())

        # Never allow empty feedback
        if not result.get("strengths"):
            result["strengths"] = ["Answer is relevant"]

        if not result.get("areas_to_improve"):
            result["areas_to_improve"] = ["Could be more detailed"]

        if not result.get("actionable_tip") or len(result["actionable_tip"]) < 10:
            result["actionable_tip"] = "Give a clearer and more structured answer."

        return result

    except:
        return {
            "score": 5,
            "strengths": ["Answered the question"],
            "areas_to_improve": ["More detail needed"],
            "actionable_tip": "Explain your answer more clearly."
        }


# -------------------------------------------------
# 🎤 VOICE FEEDBACK (REAL INTERVIEW STYLE)
# -------------------------------------------------
def generate_voice_feedback(question, transcript, scores):
    client = get_client()

    prompt = f"""
You are an interview coach.

Question:
{question}

Candidate Answer:
{transcript}

System Scores:
Content: {scores['content_score']}/10
Clarity: {scores['clarity']}/10
Structure: {scores['structure']}/10
Relevance: {scores['relevance']}/10

Give feedback in this format only:

Strengths:
- one clear strength
- one clear strength

Improvements:
- one clear improvement
- one clear improvement

Tip:
one short actionable sentence
"""

    def call():
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=250
        )
        return response.choices[0].message.content.strip()

    return safe_llm_call(call, "Feedback unavailable. Please try again.")
