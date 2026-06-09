import os
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from llm_service import generate_questions, evaluate_answer
from resume_service import extract_resume_text, analyze_resume

from speech_module.stt_engine import transcribe
from speech_module.speech_intelligence import analyze_speech
from speech_module.voice_llm_evaluator import evaluate_voice_answer

from video_module.video_engine import extract_frames
from video_module.face_analysis import analyze_frame
from video_module.video_metrics import (
    face_visibility_ratio,
    eye_contact_ratio,
    head_movement_level,
    facial_activity_level,
    engagement_score
)
from video_module.video_feedback import generate_video_feedback

# =====================================================
# APP SETUP
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "../static")),
    name="static"
)

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "../templates")
)

# =====================================================
# SESSION (SINGLE USER – FINAL YEAR SAFE)
# =====================================================
SESSION = {
    "questions": [],
    "current": 0,
    "round": "",

    # legacy (used by /end – DO NOT TOUCH)
    "scores": [],

    # NEW – used for Module 4 (fusion & report)
    "detailed_scores": [],

    "last_question": ""
}

# =====================================================
# HOME
# =====================================================
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# =====================================================
# RESUME
# =====================================================
@app.get("/resume", response_class=HTMLResponse)
def resume_page(request: Request):
    return templates.TemplateResponse("resume.html", {"request": request})

@app.post("/resume-analyze", response_class=HTMLResponse)
def resume_analyze(
    request: Request,
    resume: UploadFile = File(...),
    job_role: str = Form(...)
):
    path = "temp.pdf"
    with open(path, "wb") as f:
        f.write(resume.file.read())

    resume_text = extract_resume_text(path)
    result = analyze_resume(resume_text, job_role)
    os.remove(path)

    return templates.TemplateResponse("resume_result.html", {
        "request": request,
        "result": result
    })

# =====================================================
# PRACTICE
# =====================================================
@app.get("/practice", response_class=HTMLResponse)
def practice_select(request: Request):
    return templates.TemplateResponse("practice_select.html", {"request": request})

# =====================================================
# START INTERVIEW
# =====================================================
@app.post("/start", response_class=HTMLResponse)
def start_interview(
    request: Request,
    role: str = Form(...),
    round_type: str = Form(...)
):
    SESSION["questions"] = generate_questions(role, round_type)
    SESSION["current"] = 0
    SESSION["round"] = round_type.lower()

    SESSION["scores"] = []
    SESSION["detailed_scores"] = []

    q = SESSION["questions"][0]
    SESSION["last_question"] = q

    return templates.TemplateResponse("interview.html", {
        "request": request,
        "question": q,
        "q_no": 1,
        "total": len(SESSION["questions"]),
        "feedback": None
    })

# =====================================================
# TEXT ANSWER
# =====================================================
@app.post("/answer", response_class=HTMLResponse)
def submit_answer(request: Request, answer: str = Form(...)):
    idx = SESSION["current"]
    question = SESSION["questions"][idx]
    SESSION["last_question"] = question

    evaluation = evaluate_answer(question, answer, SESSION["round"])

    # legacy score (DO NOT REMOVE)
    SESSION["scores"].append(evaluation["score"])

    # NEW – structured storage
    SESSION["detailed_scores"].append({
        "question": question,
        "mode": "text",
        "score": evaluation["score"],
        "details": {
            "strengths": evaluation.get("strengths", []),
            "improvements": evaluation.get("areas_to_improve", []),
            "tip": evaluation.get("actionable_tip", "")
        }
    })

    return templates.TemplateResponse("interview.html", {
        "request": request,
        "question": question,
        "q_no": idx + 1,
        "total": len(SESSION["questions"]),
        "feedback": evaluation
    })

# =====================================================
# NEXT / SKIP
# =====================================================
@app.post("/next", response_class=HTMLResponse)
def next_question(request: Request):
    SESSION["current"] += 1

    if SESSION["current"] >= len(SESSION["questions"]):
        return end_practice(request)

    q = SESSION["questions"][SESSION["current"]]
    SESSION["last_question"] = q

    return templates.TemplateResponse("interview.html", {
        "request": request,
        "question": q,
        "q_no": SESSION["current"] + 1,
        "total": len(SESSION["questions"]),
        "feedback": None
    })

@app.post("/skip", response_class=HTMLResponse)
def skip_question(request: Request):
    return next_question(request)

# =====================================================
# END
# =====================================================
@app.api_route("/end", methods=["GET", "POST"], response_class=HTMLResponse)
def end_practice(request: Request):

    
    all_scores = [item["score"] for item in SESSION["detailed_scores"]]

    total = len(all_scores)

    avg = round(sum(all_scores) / total, 2) if total else 0
    text_scores = []
    voice_scores = []
    video_scores = []

    for item in SESSION["detailed_scores"]:

        if item["mode"] == "text":
            text_scores.append(item["score"])

        elif item["mode"] == "voice":
            voice_scores.append(item["score"])

        elif item["mode"] == "video":
            video_scores.append(item["score"])

    def safe_avg(lst):
        return round(sum(lst) / len(lst), 2) if lst else 0

    analytics = {
        "text_avg": safe_avg(text_scores),
        "voice_avg": safe_avg(voice_scores),
        "video_avg": safe_avg(video_scores)
    }

    # -----------------------------------------
    # Interview Insights (NEW FEATURE)
    # -----------------------------------------

    strengths = []
    weaknesses = []
    tips = []

    # Text analysis
    if analytics["text_avg"] >= 7:
        strengths.append("Clear and relevant answers")

    else:
        weaknesses.append("Improve answer structure and clarity")
        tips.append("Use the STAR method to structure your answers")

    # Voice analysis
    if analytics["voice_avg"] >= 7:
        strengths.append("Good speech fluency and confidence")

    elif analytics["voice_avg"] > 0:
        weaknesses.append("Speech fluency needs improvement")
        tips.append("Reduce filler words and maintain steady speaking pace")

    # Video analysis
    if analytics["video_avg"] >= 7:
        strengths.append("Strong eye contact and camera engagement")

    elif analytics["video_avg"] > 0:
        weaknesses.append("Improve camera presence and eye contact")
        tips.append("Keep your face centered and maintain natural eye contact")

    return templates.TemplateResponse("end.html", {
        "request": request,
        "total_questions": total,
        "average_score": avg,
        "scores": SESSION["scores"],
        "analytics": analytics,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "tips": tips
    })
# =====================================================
# 🎤 VOICE UPLOAD
# =====================================================
@app.post("/voice-upload")
async def voice_upload(
    file: UploadFile = File(...),
    question: str = Form("")
):
    try:
        os.makedirs("uploads", exist_ok=True)
        path = "uploads/input.webm"

        with open(path, "wb") as f:
            f.write(await file.read())

        stt = transcribe(path)
        transcript = stt.get("text", "")
        words = stt.get("words", [])
        duration = stt.get("duration", 0)

        if not transcript.strip():
            return {"error": "No speech detected"}

        if not question.strip():
            question = SESSION.get("last_question", "")
        speech = analyze_speech(words, duration)

        feedback = evaluate_voice_answer(
            question,
            transcript,
            speech,
            SESSION["round"]
        )
        # ------------------------------
        # SAFE SCORE CALCULATION
        # ------------------------------
        
        relevance = float(feedback.get("relevance", 0))
        clarity = float(feedback.get("clarity", 0))
        structure = float(feedback.get("structure", 0))

        fluency = float(speech.get("fluency", 0))
        confidence = float(speech.get("confidence", 0))

        overall = round(
              (relevance + clarity + structure + fluency + confidence) / 5,2)

        #override LLM score
        feedback["overall_score"] = overall
        

        # NEW – structured storage
        SESSION["detailed_scores"].append({
            "question": question,
            "mode": "voice",
            "score": feedback["overall_score"],
            "details": {
                "speech": speech,
                "relevance": feedback.get("relevance", 0),
                "clarity": feedback.get("clarity", 0),
                "structure": feedback.get("structure", 0),
                "strengths": feedback.get("strengths", []),
                "improvements": feedback.get("improvements", [])
                
            }
        })

        return {
    "transcript": transcript,

    # speech metrics
    "speech": speech,

    # overall score
    "overall_score": feedback["overall_score"],

    # content scores
    "scores": {
        "relevance": feedback["relevance"],
        "clarity": feedback["clarity"],
        "structure": feedback["structure"],
        "content_score": round(
            (feedback["relevance"] + feedback["clarity"] + feedback["structure"]) / 3, 2
        )
    },

    # NEW – speaking feedback from LLM
    "speaking_feedback": feedback.get("speaking_feedback", {}),

    "strengths": feedback.get("strengths", []),
    "improvements": feedback.get("improvements", []),
    "tip": feedback.get("tip", "")
}

    except Exception as e:
        print("VOICE ERROR:", e)
        return {"error": "Voice processing failed"}


# =====================================================
# 🎥 VIDEO UPLOAD
# =====================================================
@app.post("/video-upload")
async def video_upload(
    file: UploadFile = File(...),
    question: str = Form("")
):
    try:
        os.makedirs("uploads", exist_ok=True)
        video_path = "uploads/video_input.webm"

        with open(video_path, "wb") as f:
            f.write(await file.read())

        stt = transcribe(video_path)
        transcript = stt.get("text", "")
        words = stt.get("words", [])
        duration = stt.get("duration", 0)

        if not transcript.strip():
            return {"error": "No speech detected in video"}

        if not question.strip():
            question = SESSION.get("last_question", "")

        # -------------------------------------------------
        # LLM CONTENT EVALUATION
        # -------------------------------------------------
        speech = analyze_speech(words, duration)

        content = evaluate_voice_answer(
            question,
            transcript,
            speech,
            SESSION["round"]
        )
        # ---------------------------------------
        # SAFE CONTENT SCORE (ignore LLM overall)
        # ---------------------------------------

        relevance = float(content.get("relevance", 0))
        clarity = float(content.get("clarity", 0))
        structure = float(content.get("structure", 0))

        content_score = round((relevance + clarity + structure) / 3, 2)

        # -------------------------------------------------
        # VIDEO ANALYSIS
        # -------------------------------------------------
        frames = extract_frames(video_path, fps=1)
        frame_results = [analyze_frame(f["frame"]) for f in frames]

        face_ratio = face_visibility_ratio(frame_results)
        eye_ratio = eye_contact_ratio(frame_results)
        head_level = head_movement_level(frame_results)
        facial_level = facial_activity_level(frame_results)
        engage = engagement_score(face_ratio, eye_ratio, head_level)
        # ---------------------------------------
        # FINAL VIDEO SCORE
        # ---------------------------------------

        overall_video_score = round(
        (content_score * 0.7) + (engage * 0.3),2)

        video_metrics = {
            "face_visibility": face_ratio,
            "eye_contact": eye_ratio,
            "head_movement": head_level,
            "facial_activity": facial_level,
            "engagement_score": engage
        }

        # -------------------------------------------------
        # VIDEO FEEDBACK (NEW STRUCTURE)
        # -------------------------------------------------
        video_eval = generate_video_feedback(video_metrics)

        video_score = video_eval["video_score"]
        video_feedback = video_eval["feedback"]

        # -------------------------------------------------
        # STORE FOR FINAL REPORT
        # -------------------------------------------------
        SESSION["detailed_scores"].append({
            "question": question,
            "mode": "video",
            "score": overall_video_score,
           
            "details": {
                "content": content,
                "video_metrics": video_metrics,
                "video_feedback": video_feedback,
                "video_score": video_score
            }
        })

        # -------------------------------------------------
        # RESPONSE TO FRONTEND
        # -------------------------------------------------
        return {
            "mode": "video",
            "transcript": transcript,
            "content_evaluation": {
                "relevance": content["relevance"],
                "clarity": content["clarity"],
                "structure": content["structure"],
                "overall_score": content["overall_score"],
                "strengths": content["strengths"],
                "improvements": content["improvements"],
                "tip": content["tip"]
            },
            "video_metrics": video_metrics,
            "video_feedback": video_feedback,
            "video_score": video_score
        }

    except Exception as e:
        print("VIDEO ERROR:", e)
        return {"error": "Video processing failed"}
