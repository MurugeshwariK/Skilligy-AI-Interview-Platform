import pdfplumber
import os
from groq import Groq

def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------------- EXTRACT TEXT ----------------
def extract_resume_text(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# ---------------- ANALYZE RESUME ----------------
def analyze_resume(resume_text: str, job_role: str):
    client = get_client()

    resume_text = resume_text[:3500]  # token safety

    prompt = f"""
You are an AI career assistant.

Analyze the resume for the given job role.

Resume:
{resume_text}

Job Role:
{job_role}

Respond STRICTLY in this format:

Match Percentage: <number>%
Matching Skills:
- skill 1
- skill 2

Missing Skills:
- skill 1
- skill 2

Suggestions:
- suggestion 1
- suggestion 2
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500
    )

    return response.choices[0].message.content
