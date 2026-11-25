import os
from typing import Dict, List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import engine, Base, get_db, SessionLocal
from models import (
    User, StudentProfile, JobRole, Assessment, AssessmentQuestion,
    AssessmentResult, SkillGapReport, LearningResource, LearningProgress,
    Project, ProjectSubmission, ExperienceModule, ProgressHistory
)
from auth import hash_password, verify_password, create_access_token, get_current_user, require_admin
from gap_engine import analyze_skill_gap, ROLE_BENCHMARKS
from ai_engine import generate_ai_skill_gap_insights, generate_career_chat_reply, check_rate_limit
from seed_data import seed_database

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CareerX AI Employability & Skill Intelligence Platform", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


# -------------------- SCHEMAS --------------------

class RegisterInput(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    target_role: str = "Data Analyst"
    college: str = ""
    degree: str = "BCA"
    semester: str = "3rd"
    cgpa: float = 0.0


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdateInput(BaseModel):
    full_name: Optional[str] = None
    college: Optional[str] = None
    degree: Optional[str] = None
    semester: Optional[str] = None
    cgpa: Optional[float] = None
    target_role: Optional[str] = None
    career_interests: Optional[str] = None
    certifications: Optional[List[str]] = None
    existing_projects: Optional[List[str]] = None
    demonstrated_skills: Optional[Dict[str, int]] = None


class SkillInput(BaseModel):
    target_role: str
    demonstrated_skills: Dict[str, int]


class AssessmentSubmitInput(BaseModel):
    role_title: str
    answers: Dict[int, str]  # question_id -> selected_answer


class LearningToggleInput(BaseModel):
    skill_name: str
    topic: str
    completed: bool


class ProjectSubmitInput(BaseModel):
    project_id: int
    repo_or_demo_url: str
    notes: str = ""


class ExperienceSubmitInput(BaseModel):
    module_id: int
    response_text: str


class ChatInput(BaseModel):
    message: str
    target_role: str = "Data Analyst"
    readiness_score: int = 0
    top_gaps: List[str] = []


# -------------------- CORE & HEALTH ENDPOINTS --------------------

@app.get("/api/health")
def health():
    return {"status": "CareerX v2.0 Backend Live", "roles_count": len(ROLE_BENCHMARKS)}


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    frontend_path = Path(__file__).parent / "frontend" / "index.html"
    if frontend_path.exists():
        return HTMLResponse(content=frontend_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>CareerX API Live</h1><p>Visit /docs for interactive API documentation.</p>")


@app.get("/roles")
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(JobRole).all()
    if not roles:
        return {"roles": list(ROLE_BENCHMARKS.keys()), "details": []}
    details = []
    for r in roles:
        reqs = {req.skill_name: req.required_score for req in r.requirements}
        details.append({
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "responsibilities": r.responsibilities,
            "tools": r.tools,
            "preferred_skills": r.preferred_skills,
            "readiness_threshold": r.readiness_threshold,
            "recommended_projects": r.recommended_projects,
            "roadmap_steps": r.roadmap_steps,
            "required_skills": reqs,
        })
    return {"roles": [r.title for r in roles], "details": details}


# -------------------- AUTHENTICATION & PROFILE --------------------

@app.post("/auth/register")
def register(data: RegisterInput, db: Session = Depends(get_db)):
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        full_name=data.full_name.strip(),
        email=data.email.lower().strip(),
        password_hash=hash_password(data.password),
        role="student",
    )
    db.add(user)
    db.flush()

    default_skills = {k: 50 for k in ROLE_BENCHMARKS.get(data.target_role, ROLE_BENCHMARKS["Data Analyst"])["skills"]}
    profile = StudentProfile(
        user_id=user.id,
        college=data.college,
        degree=data.degree,
        semester=data.semester,
        cgpa=data.cgpa,
        target_role=data.target_role,
        demonstrated_skills=default_skills,
    )
    db.add(profile)
    db.commit()

    token = create_access_token(user.id, user.email, user.role)
    return {
        "token": token,
        "user": {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role},
    }


@app.post("/auth/login")
def login(data: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id, user.email, user.role)
    return {
        "token": token,
        "user": {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role},
    }


@app.get("/profile/me")
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    history = (
        db.query(ProgressHistory)
        .filter(ProgressHistory.user_id == current_user.id)
        .order_by(ProgressHistory.recorded_at.asc())
        .all()
    )
    learning = db.query(LearningProgress).filter(LearningProgress.user_id == current_user.id).all()
    submissions = db.query(ProjectSubmission).filter(ProjectSubmission.user_id == current_user.id).all()

    return {
        "user": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "role": current_user.role,
        },
        "profile": {
            "college": profile.college if profile else "",
            "degree": profile.degree if profile else "",
            "semester": profile.semester if profile else "",
            "cgpa": profile.cgpa if profile else 0.0,
            "target_role": profile.target_role if profile else "Data Analyst",
            "career_interests": profile.career_interests if profile else "",
            "certifications": profile.certifications if profile else [],
            "existing_projects": profile.existing_projects if profile else [],
            "demonstrated_skills": profile.demonstrated_skills if profile else {},
        },
        "history": [
            {
                "id": h.id,
                "role_title": h.role_title,
                "readiness_score": h.readiness_score,
                "skill_snapshot": h.skill_snapshot,
                "recorded_at": h.recorded_at.isoformat(),
            }
            for h in history
        ],
        "completed_topics": [f"{l.skill_name}::{l.topic}" for l in learning if l.completed],
        "submissions_count": len(submissions),
    }


@app.put("/profile/me")
def update_my_profile(
    data: ProfileUpdateInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.full_name is not None:
        current_user.full_name = data.full_name.strip()

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.add(profile)

    for field in ["college", "degree", "semester", "cgpa", "target_role", "career_interests", "certifications", "existing_projects", "demonstrated_skills"]:
        val = getattr(data, field)
        if val is not None:
            setattr(profile, field, val)

    db.commit()
    return {"status": "Profile updated successfully"}


# -------------------- SKILL GAP & AI ANALYSIS --------------------

@app.post("/analyze")
def analyze(data: SkillInput):
    try:
        return analyze_skill_gap(data.target_role, data.demonstrated_skills)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@app.post("/analyze/ai")
def analyze_with_ai(
    data: SkillInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not check_rate_limit(f"ai_{current_user.id}"):
        raise HTTPException(status_code=429, detail="AI rate limit reached. Please wait 60 seconds.")

    try:
        gap_report = analyze_skill_gap(data.target_role, data.demonstrated_skills)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    context = ""
    if profile:
        profile.target_role = data.target_role
        profile.demonstrated_skills = data.demonstrated_skills
        context = f"{profile.degree} Sem {profile.semester}, CGPA {profile.cgpa}, Interests: {profile.career_interests}"

    ai_insights = generate_ai_skill_gap_insights(gap_report, context)

    db.add(
        SkillGapReport(
            user_id=current_user.id,
            role_title=data.target_role,
            readiness_score=gap_report["job_readiness_score"],
            gap_breakdown=gap_report["skills"],
            ai_analysis=ai_insights,
        )
    )
    db.add(
        ProgressHistory(
            user_id=current_user.id,
            role_title=data.target_role,
            readiness_score=gap_report["job_readiness_score"],
            skill_snapshot=data.demonstrated_skills,
        )
    )
    db.commit()

    return {**gap_report, "ai_insights": ai_insights}


# -------------------- ASSESSMENTS & REASSESSMENT --------------------

@app.get("/assessments/{role_title}")
def get_assessment(role_title: str, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.role_title == role_title).first()
    if not assessment:
        # Fallback to Data Analyst assessment if role-specific questions are not yet seeded
        assessment = db.query(Assessment).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="No assessment found")

    return {
        "id": assessment.id,
        "role_title": assessment.role_title,
        "title": assessment.title,
        "duration_minutes": assessment.duration_minutes,
        "questions": [
            {
                "id": q.id,
                "skill_name": q.skill_name,
                "question_type": q.question_type,
                "prompt": q.prompt,
                "options": q.options,
            }
            for q in assessment.questions
        ],
    }


@app.post("/assessments/submit")
def submit_assessment(
    data: AssessmentSubmitInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    questions = db.query(AssessmentQuestion).filter(AssessmentQuestion.id.in_(list(data.answers.keys()))).all()
    if not questions:
        raise HTTPException(status_code=400, detail="No valid answers submitted")

    skill_totals: Dict[str, List[int]] = {}
    review = []
    correct_count = 0

    for q in questions:
        chosen = data.answers.get(q.id, "")
        is_correct = chosen.strip() == q.correct_answer.strip()
        if is_correct:
            correct_count += 1
        skill_totals.setdefault(q.skill_name, []).append(100 if is_correct else 35)
        review.append({
            "question_id": q.id,
            "skill_name": q.skill_name,
            "prompt": q.prompt,
            "your_answer": chosen,
            "correct_answer": q.correct_answer,
            "is_correct": is_correct,
            "explanation": q.explanation,
        })

    measured_skills = {skill: round(sum(vals) / len(vals)) for skill, vals in skill_totals.items()}
    overall_score = round((correct_count / len(questions)) * 100)

    # Merge measured assessment scores into student profile
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    merged_skills = dict(profile.demonstrated_skills) if profile and profile.demonstrated_skills else {}
    merged_skills.update(measured_skills)

    if profile:
        profile.target_role = data.role_title
        profile.demonstrated_skills = merged_skills

    gap_report = analyze_skill_gap(data.role_title, merged_skills)

    db.add(
        AssessmentResult(
            user_id=current_user.id,
            role_title=data.role_title,
            overall_score=overall_score,
            skill_scores=measured_skills,
            ai_feedback=f"Scored {correct_count}/{len(questions)} ({overall_score}%). Updated Job Readiness: {gap_report['job_readiness_score']}/100.",
        )
    )
    db.add(
        ProgressHistory(
            user_id=current_user.id,
            role_title=data.role_title,
            readiness_score=gap_report["job_readiness_score"],
            skill_snapshot=merged_skills,
        )
    )
    db.commit()

    return {
        "assessment_score": overall_score,
        "correct_count": correct_count,
        "total_questions": len(questions),
        "measured_skills": measured_skills,
        "updated_readiness": gap_report,
        "review": review,
    }


# -------------------- LEARNING, PROJECTS & CAREER EXPERIENCE --------------------

@app.get("/learning/resources")
def get_learning_resources(db: Session = Depends(get_db)):
    resources = db.query(LearningResource).all()
    return [
        {
            "id": r.id,
            "skill_name": r.skill_name,
            "title": r.title,
            "provider": r.provider,
            "resource_type": r.resource_type,
            "url": r.url,
            "estimated_hours": r.estimated_hours,
        }
        for r in resources
    ]


@app.post("/learning/progress")
def toggle_learning_progress(
    data: LearningToggleInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(LearningProgress)
        .filter(
            LearningProgress.user_id == current_user.id,
            LearningProgress.skill_name == data.skill_name,
            LearningProgress.topic == data.topic,
        )
        .first()
    )
    if not item:
        item = LearningProgress(
            user_id=current_user.id,
            skill_name=data.skill_name,
            topic=data.topic,
            completed=data.completed,
        )
        db.add(item)
    else:
        item.completed = data.completed

    # Reward completed learning topic with +5 skill boost (capped at 100)
    if data.completed:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if profile:
            skills = dict(profile.demonstrated_skills or {})
            current_val = int(skills.get(data.skill_name, 50))
            skills[data.skill_name] = min(100, current_val + 5)
            profile.demonstrated_skills = skills

    db.commit()
    return {"status": "Learning progress saved"}


@app.get("/projects")
def list_projects(role_title: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Project)
    if role_title:
        filtered = q.filter(Project.role_title == role_title).all()
        projects = filtered if filtered else q.all()
    else:
        projects = q.all()

    return [
        {
            "id": p.id,
            "role_title": p.role_title,
            "title": p.title,
            "description": p.description,
            "technologies": p.technologies,
            "skills_developed": p.skills_developed,
            "difficulty": p.difficulty,
            "expected_outcome": p.expected_outcome,
            "roadmap": p.roadmap,
        }
        for p in projects
    ]


@app.post("/projects/submit")
def submit_project(
    data: ProjectSubmitInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = ProjectSubmission(
        user_id=current_user.id,
        project_id=data.project_id,
        repo_or_demo_url=data.repo_or_demo_url.strip(),
        notes=data.notes.strip(),
    )
    db.add(sub)
    db.commit()
    return {"status": "Project submission recorded", "submission_id": sub.id}


@app.get("/experience/modules")
def list_experience_modules(db: Session = Depends(get_db)):
    mods = db.query(ExperienceModule).all()
    return [
        {
            "id": m.id,
            "role_title": m.role_title,
            "title": m.title,
            "simulation_badge": m.simulation_badge,
            "scenario": m.scenario,
            "sample_dataset": m.sample_dataset,
            "tasks": m.tasks,
            "deliverable_prompt": m.deliverable_prompt,
        }
        for m in mods
    ]


@app.post("/experience/submit")
def submit_experience_assignment(
    data: ExperienceSubmitInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if len(data.response_text.strip()) < 15:
        raise HTTPException(status_code=400, detail="Please provide a complete analysis before submitting.")
    mod = db.query(ExperienceModule).filter(ExperienceModule.id == data.module_id).first()
    if not mod:
        raise HTTPException(status_code=404, detail="Experience module not found")

    return {
        "status": "Simulation Deliverable Evaluated",
        "badge": mod.simulation_badge,
        "feedback": f"Great structured deliverable for '{mod.title}'. Retake your CareerX Assessment to verify your updated readiness score!",
    }


# -------------------- AI CAREER MENTOR CHAT --------------------

@app.post("/ai/chat")
def ai_career_chat(data: ChatInput, current_user: User = Depends(get_current_user)):
    if not check_rate_limit(f"chat_{current_user.id}"):
        raise HTTPException(status_code=429, detail="Too many chat requests. Please wait 60 seconds.")
    return generate_career_chat_reply(data.message, data.target_role, data.readiness_score, data.top_gaps)


# -------------------- ADMIN DASHBOARD (ROLE-PROTECTED) --------------------

@app.get("/admin/analytics")
def admin_analytics(admin_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    total_students = db.query(User).filter(User.role == "student").count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_assessments = db.query(AssessmentResult).count()
    total_submissions = db.query(ProjectSubmission).count()

    profiles = db.query(StudentProfile).all()
    role_counts: Dict[str, int] = {}
    for p in profiles:
        role_counts[p.target_role] = role_counts.get(p.target_role, 0) + 1

    users = db.query(User).order_by(User.created_at.desc()).limit(25).all()
    return {
        "total_registered_students": total_students,
        "active_users": active_users,
        "total_assessments_taken": total_assessments,
        "total_project_submissions": total_submissions,
        "popular_job_roles": role_counts,
        "users": [
            {"id": u.id, "full_name": u.full_name, "email": u.email, "role": u.role, "is_active": u.is_active}
            for u in users
        ],
    }