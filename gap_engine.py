from typing import Dict, List

ROLE_BENCHMARKS: Dict[str, Dict[str, int]] = {
    "Data Analyst": {
        "Excel": 85,
        "Python": 75,
        "Stats": 70,
        "SQL": 90,
        "Power BI": 80,
    },
    "AI/ML Engineer": {
        "Python": 90,
        "SQL": 75,
        "Machine Learning": 85,
        "Deep Learning": 80,
        "LLM / NLP": 85,
    },
}

PROJECT_RECOMMENDATIONS: Dict[str, str] = {
    "SQL": "Sales Analytical Dashboard banao (SQL + Power BI)",
    "Power BI": "Revenue & Churn BI Dashboard banao",
    "Python": "Pandas se Data Cleaning script banao",
    "Stats": "Sales data par A/B testing aur analysis karo",
    "Excel": "Excel mein Sales & Expense tracker banao",
    "LLM / NLP": "Notes ya PDF se sawal poochne wala AI tool banao",
}


def analyze_skill_gap(target_role: str, demonstrated_skills: Dict[str, int]) -> dict:
    benchmarks = ROLE_BENCHMARKS.get(target_role)
    if not benchmarks:
        raise ValueError(f"'{target_role}' role abhi list mein nahi hai.")

    skill_breakdown: List[dict] = []
    top_gaps: List[dict] = []

    total_required = sum(benchmarks.values())
    total_achieved = 0

    for skill, required in benchmarks.items():
        user_score = demonstrated_skills.get(skill, 0)
        gap = max(0, required - user_score)

        total_achieved += min(user_score, required)

        if gap >= 25:
            status = "Major Gap"
        elif gap >= 10:
            status = "Medium Gap"
        elif gap > 0:
            status = "Minor Gap"
        else:
            status = "Ready"

        skill_breakdown.append({
            "skill": skill,
            "required": required,
            "demonstrated": user_score,
            "gap": gap,
            "status": status,
        })

        if gap > 0:
            top_gaps.append({"skill": skill, "gap": gap, "status": status})

    top_gaps.sort(key=lambda x: x["gap"], reverse=True)
    priority_actions = [item["skill"] for item in top_gaps[:3]]
    readiness_score = round((total_achieved / total_required) * 100)

    top_skill = top_gaps[0]["skill"] if top_gaps else None
    recommended_project = (
        PROJECT_RECOMMENDATIONS.get(top_skill, f"{top_skill} par ek real project banao")
        if top_skill
        else "Ab tum internship/project ke liye kaafi ready ho!"
    )

    return {
        "target_role": target_role,
        "job_readiness_score": readiness_score,
        "skills": skill_breakdown,
        "priority_actions": priority_actions,
        "top_skills_gap": top_gaps[:3],
        "recommended_project": recommended_project,
    }