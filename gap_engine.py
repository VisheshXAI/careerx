from typing import Dict, Any

ROLE_BENCHMARKS: Dict[str, Dict[str, Any]] = {
    "Data Analyst": {
        "skills": {"Excel": 85, "Python": 75, "Stats": 70, "SQL": 90, "Power BI": 80},
        "project": "Revenue & Churn BI Dashboard using SQL, Python and Power BI",
    },
    "Data Scientist": {
        "skills": {"Python": 88, "Stats": 85, "Machine Learning": 85, "SQL": 80, "Feature Engineering": 78},
        "project": "End-to-End Customer Lifetime Value & Churn Prediction Pipeline",
    },
    "AI/ML Engineer": {
        "skills": {"Python": 90, "SQL": 70, "Machine Learning": 85, "Deep Learning": 80, "LLM / NLP": 82},
        "project": "Production RAG Document Intelligence Assistant with FastAPI & Vector Search",
    },
    "Software Developer": {
        "skills": {"DSA": 85, "Python / Java": 85, "Git & CI/CD": 75, "Databases": 80, "System Design": 72},
        "project": "Scalable Task & Workflow Engine with REST APIs and Automated Testing",
    },
    "Frontend Developer": {
        "skills": {"HTML & CSS": 90, "JavaScript": 88, "React.js": 85, "API Integration": 80, "UI/UX & Performance": 78},
        "project": "Interactive Analytics SaaS Workspace with Real-Time State & Charts",
    },
    "Backend Developer": {
        "skills": {"Python / Node": 88, "REST APIs": 88, "SQL & PostgreSQL": 85, "Auth & Security": 80, "Docker & Cloud": 75},
        "project": "Multi-Tenant SaaS Backend with JWT Auth, Rate Limiting & PostgreSQL",
    },
    "Business Analyst": {
        "skills": {"Excel": 90, "SQL": 78, "BI & Visualization": 82, "Requirement Gathering": 85, "Stakeholder Communication": 85},
        "project": "E-Commerce Conversion Funnel & Pricing Strategy Case Study",
    },
    "Cloud Engineer": {
        "skills": {"Linux": 85, "AWS / GCP": 85, "Docker & Kubernetes": 82, "Terraform / IaC": 78, "Networking & Security": 80},
        "project": "Zero-Downtime Containerized Microservice Deployment with CI/CD",
    },
    "Cybersecurity Analyst": {
        "skills": {"Networking": 88, "Linux & Scripting": 82, "SIEM & Threat Detection": 85, "Vulnerability Assessment": 82, "Incident Response": 80},
        "project": "Automated Log Anomaly Detector & Web Vulnerability Audit Suite",
    },
}


def analyze_skill_gap(target_role: str, demonstrated_skills: Dict[str, int]) -> Dict[str, Any]:
    if target_role not in ROLE_BENCHMARKS:
        raise ValueError(f"Unsupported role: {target_role}")

    benchmark = ROLE_BENCHMARKS[target_role]["skills"]
    skills_report = []
    total_ratio = 0.0

    for skill, required in benchmark.items():
        demo = max(0, min(100, int(demonstrated_skills.get(skill, 0))))
        gap = max(0, required - demo)
        ratio = min(1.0, demo / required) if required > 0 else 1.0
        total_ratio += ratio

        if gap == 0:
            status = "Ready"
        elif gap <= 15:
            status = "Minor Gap"
        else:
            status = "Major Gap"

        skills_report.append({
            "skill": skill,
            "demonstrated": demo,
            "required": required,
            "gap": gap,
            "status": status,
        })

    readiness_score = round((total_ratio / len(benchmark)) * 100)
    top_gaps = sorted([s for s in skills_report if s["gap"] > 0], key=lambda x: x["gap"], reverse=True)
    strongest = sorted([s for s in skills_report if s["gap"] <= 10], key=lambda x: x["demonstrated"], reverse=True)

    return {
        "target_role": target_role,
        "job_readiness_score": readiness_score,
        "skills": skills_report,
        "top_skills_gap": top_gaps,
        "strongest_skills": strongest[:3],
        "recommended_project": ROLE_BENCHMARKS[target_role]["project"],
    }