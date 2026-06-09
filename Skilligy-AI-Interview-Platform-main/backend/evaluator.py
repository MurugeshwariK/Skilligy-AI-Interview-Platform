cd Desktop\Skilligy-AI-Interview-Platform-maindef evaluate_hr_answer(answer: str):
    score = 0
    strengths = []
    gaps = []

    word_count = len(answer.split())

    # Clarity
    if word_count > 60:
        score += 2
        strengths.append("Clear and detailed explanation")
    else:
        gaps.append("Answer could be more detailed")

    # Structure (STAR)
    keywords = ["situation", "task", "action", "result"]
    if any(k in answer.lower() for k in keywords):
        score += 3
        strengths.append("Good structure using real examples")
    else:
        gaps.append("Could use STAR method")

    # Relevance
    score += 3

    # Learning
    if "learn" in answer.lower() or "improve" in answer.lower():
        score += 2
        strengths.append("Shows reflection and learning")

    score = min(score, 10)

    return score, strengths, gaps
