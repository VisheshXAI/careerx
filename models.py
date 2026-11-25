from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="student")  # student | admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    profile = relationship("StudentProfile", back_populates="user", uselist=False)
    assessments = relationship("AssessmentResult", back_populates="user")
    history = relationship("ProgressHistory", back_populates="user")


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    college = Column(String(180), default="")
    degree = Column(String(120), default="BCA / B.Tech")
    semester = Column(String(40), default="3rd")
    cgpa = Column(Float, default=0.0)
    target_role = Column(String(100), default="Data Analyst")
    career_interests = Column(Text, default="")
    certifications = Column(JSON, default=list)
    existing_projects = Column(JSON, default=list)
    demonstrated_skills = Column(JSON, default=dict)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="profile")


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), unique=True, nullable=False)
    category = Column(String(80), default="Technical")


class JobRole(Base):
    __tablename__ = "job_roles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    responsibilities = Column(JSON, default=list)
    tools = Column(JSON, default=list)
    preferred_skills = Column(JSON, default=list)
    readiness_threshold = Column(Integer, default=75)
    recommended_projects = Column(JSON, default=list)
    roadmap_steps = Column(JSON, default=list)

    requirements = relationship("JobRequirement", back_populates="job_role", cascade="all, delete-orphan")


class JobRequirement(Base):
    __tablename__ = "job_requirements"
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("job_roles.id"), nullable=False)
    skill_name = Column(String(80), nullable=False)
    required_score = Column(Integer, nullable=False)
    weight = Column(Float, default=1.0)

    job_role = relationship("JobRole", back_populates="requirements")


class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True, index=True)
    role_title = Column(String(100), index=True, nullable=False)
    title = Column(String(160), nullable=False)
    duration_minutes = Column(Integer, default=15)

    questions = relationship("AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    skill_name = Column(String(80), nullable=False)
    question_type = Column(String(30), default="mcq")  # mcq | coding | practical
    prompt = Column(Text, nullable=False)
    options = Column(JSON, default=list)
    correct_answer = Column(String(255), nullable=False)
    explanation = Column(Text, default="")

    assessment = relationship("Assessment", back_populates="questions")


class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_title = Column(String(100), nullable=False)
    overall_score = Column(Float, nullable=False)
    skill_scores = Column(JSON, default=dict)
    ai_feedback = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="assessments")


class SkillGapReport(Base):
    __tablename__ = "skill_gap_reports"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_title = Column(String(100), nullable=False)
    readiness_score = Column(Float, nullable=False)
    gap_breakdown = Column(JSON, default=list)
    ai_analysis = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)


class LearningResource(Base):
    __tablename__ = "learning_resources"
    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String(80), index=True, nullable=False)
    title = Column(String(180), nullable=False)
    provider = Column(String(100), default="CareerX Curated")
    resource_type = Column(String(50), default="Course")
    url = Column(String(255), default="#")
    estimated_hours = Column(Integer, default=6)


class LearningProgress(Base):
    __tablename__ = "learning_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_name = Column(String(80), nullable=False)
    topic = Column(String(180), nullable=False)
    completed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    role_title = Column(String(100), index=True, nullable=False)
    title = Column(String(180), nullable=False)
    description = Column(Text, nullable=False)
    technologies = Column(JSON, default=list)
    skills_developed = Column(JSON, default=list)
    difficulty = Column(String(40), default="Intermediate")
    expected_outcome = Column(Text, default="")
    roadmap = Column(JSON, default=list)


class ProjectSubmission(Base):
    __tablename__ = "project_submissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    repo_or_demo_url = Column(String(255), nullable=False)
    notes = Column(Text, default="")
    status = Column(String(40), default="Submitted")
    submitted_at = Column(DateTime, default=utcnow)


class ExperienceModule(Base):
    __tablename__ = "experience_modules"
    id = Column(Integer, primary_key=True, index=True)
    role_title = Column(String(100), index=True, nullable=False)
    title = Column(String(180), nullable=False)
    simulation_badge = Column(String(120), default="Simulated Industry Experience (Not an Actual Company Internship)")
    scenario = Column(Text, nullable=False)
    sample_dataset = Column(JSON, default=list)
    tasks = Column(JSON, default=list)
    deliverable_prompt = Column(Text, nullable=False)


class ProgressHistory(Base):
    __tablename__ = "progress_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_title = Column(String(100), nullable=False)
    readiness_score = Column(Float, nullable=False)
    skill_snapshot = Column(JSON, default=dict)
    recorded_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="history")