# ============================================================
# Real Interview Speech Intelligence Engine
# ============================================================

FILLERS = {
    "um", "uh", "umm", "er", "ah",
    "like", "so", "actually",
    "you", "know", "basically"
}

# ------------------------------------------------------------
# Clean Whisper word
# ------------------------------------------------------------
def clean(word):
    return word.lower().strip(" ,.!?")

# ------------------------------------------------------------
# Speaking Rate (WPM)
# ------------------------------------------------------------
def speaking_rate(words, duration):
    if not words or duration <= 0:
        return 0
    return round((len(words) / duration) * 60, 1)

# ------------------------------------------------------------
# Pause Detection
# ------------------------------------------------------------
def detect_pauses(words):
    thinking = 0
    hesitation = 0

    for i in range(len(words) - 1):
        gap = words[i+1]["start"] - words[i]["end"]

        # Natural thinking pause
        if 0.8 <= gap <= 2.0:
            thinking += 1
        # Long hesitation (bad)
        elif gap > 2.0:
            hesitation += 1

    return thinking, hesitation

# ------------------------------------------------------------
# Filler Detection
# ------------------------------------------------------------
def count_fillers(words):
    count = 0
    for w in words:
        if clean(w["word"]) in FILLERS:
            count += 1
    return count

# ------------------------------------------------------------
# Fluency (0–10)
# ------------------------------------------------------------
def fluency_score(wpm, hesitation, fillers):
    score = 10

    # Speaking speed
    if wpm < 90:
        score -= 2
    elif wpm > 180:
        score -= 1.5

    # Real penalties
    score -= hesitation * 1.2
    score -= fillers * 0.6

    return round(max(0, min(10, score)), 1)

# ------------------------------------------------------------
# Confidence (0–10)
# ------------------------------------------------------------
def confidence_score(wpm, hesitation, fillers):
    score = 10

    # Too slow or too fast hurts confidence
    if wpm < 100:
        score -= 2
    if wpm > 180:
        score -= 1.5

    score -= hesitation * 1.0
    score -= fillers * 0.7

    return round(max(0, min(10, score)), 1)

# ------------------------------------------------------------
# Final Speech Analyzer
# ------------------------------------------------------------
def analyze_speech(words, duration):
    if not words or duration <= 0:
        return {
            "wpm": 0,
            "thinking_pauses": 0,
            "hesitation_pauses": 0,
            "fillers": 0,
            "fluency": 0,
            "confidence": 0
        }

    wpm = speaking_rate(words, duration)
    thinking, hesitation = detect_pauses(words)
    fillers = count_fillers(words)

    fluency = fluency_score(wpm, hesitation, fillers)
    confidence = confidence_score(wpm, hesitation, fillers)

    return {
        "wpm": wpm,
        "thinking_pauses": thinking,
        "hesitation_pauses": hesitation,
        "fillers": fillers,
        "fluency": fluency,
        "confidence": confidence
    }
