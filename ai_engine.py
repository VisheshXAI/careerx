import os
import json
import time
from typing import Dict, Any, List

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Simple in-memory per-user rate limiter (max 15 AI requests per minute)
_RATE_BUCKET: Dict[str, List[float]] = {}


def check_rate_limit(identifier: str, limit: int = 15, window_sec: int = 60) -> bool:
    now = time.time()
    timestamps = [t for t in _RATE_BUCKET.get(identifier, []) if now - t < window_sec]
    if len(timestamps) >= limit:
        return False
    timestamps.append(now)
    _RATE_BUCKET[identifier] = timestamps
    return True


def _call_gemini_json(prompt: str) -> Dict[str, Any]:
    if not GEMINI_API_KEY:
        return {}
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        return json.loads(response.text)
    except Exception:
        return {}


def _call_gemini_text(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return ""
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        return (response.text or "").strip()
    except Exception:
        return ""


def generate_ai_skill_gap_insights(gap_report: Dict[str, Any], student_context: str = "") -> Dict[str, Any]:
    role = gap_report["target_role"]
    score = gap_report["job_readiness_score"]
    gaps = gap_report["top_skills_gap"]

    prompt = f"""
    You are CareerX AI Career Architect. Analyze this verified student skill gap report.
    Target Role: {role}
    Readiness Score: {score}/100
    Top Skill Gaps: {json.dumps(gaps)}
    Student Background: {student_context or "Undergraduate CS/AI student"}

    Return strictly valid JSON with keys:
    - "executive_summary": 2 concise sentences explaining readiness and biggest lever.
    - "gap_explanations": list of objects {{"skill": str, "why_it_matters": str, "action_plan": str}} for each gap.
    - "weekly_roadmap": list of 4 objects {{"week": int, "focus": str, "target_deliverable": str}}.
    """

    ai_json = _call_gemini_json(prompt)
    if ai_json and "executive_summary" in ai_json:
        ai_json["ai_powered"] = True
        return ai_json

    # Deterministic structured fallback if GEMINI_API_KEY is not configured yet
    gap_explanations = []
    for g in gaps:
        gap_explanations.append({
            "skill": g["skill"],
            "why_it_matters": f"{g['skill']} is a core benchmark requirement ({g['required']}%) for {role} workflows.",
            "action_plan": f"Close the {g['gap']}% gap by completing 2 hands-on drills and applying {g['skill']} inside a portfolio project.",
        })

    weekly_roadmap = [
        {"week": 1, "focus": gaps[0]["skill"] if gaps else "Core Foundations", "target_deliverable": "Complete core concept exercises & mini-lab"},
        {"week": 2, "focus": gaps[1]["skill"] if len(gaps) > 1 else "Applied Problem Solving", "target_deliverable": "Build functional data/code module"},
        {"week": 3, "focus": "End-to-End Integration", "target_deliverable": gap_report["recommended_project"]},
        {"week": 4, "focus": "Reassessment & Portfolio Review", "target_deliverable": "Retake CareerX assessment and reach >=80 readiness"},
    ]

    return {
        "ai_powered": False,
        "notice": "Set GEMINI_API_KEY in Render environment variables to enable live Gemini generative coaching.",
        "executive_summary": f"Your current readiness for {role} is {score}/100. Focusing on {gaps[0]['skill'] if gaps else 'advanced projects'} will yield the fastest readiness boost.",
        "gap_explanations": gap_explanations,
        "weekly_roadmap": weekly_roadmap,
    }


def generate_career_chat_reply(message: str, role: str, readiness_score: int, top_gaps: List[str]) -> Dict[str, Any]:
    prompt = f"""
    You are CareerX AI Mentor. Answer the student's career question concisely and practically.
    Student Target Role: {role}
    Current Readiness Score: {readiness_score}/100
    Priority Skill Gaps: {', '.join(top_gaps) if top_gaps else 'None'}
    Student Question: {message}
    """
    text = _call_gemini_text(prompt)
    if text:
        return {"reply": text, "ai_powered": True}

    gap_str = ", ".join(top_gaps) if top_gaps else "system-level projects"
    return {
        "reply": (
            f"For {role} (current readiness: {readiness_score}/100), prioritize closing your gaps in {gap_str}. "
            f"Start by completing the Career Experience simulation lab for {role}, build a measurable project, and retake the assessment to verify score growth. "
            f"(Tip: Add GEMINI_API_KEY in backend environment variables for full conversational Gemini coaching.)"
        ),
        "ai_powered": False,
    }