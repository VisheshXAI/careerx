from sqlalchemy.orm import Session
from models import (
    User, StudentProfile, JobRole, JobRequirement,
    Assessment, AssessmentQuestion, LearningResource, Project, ExperienceModule
)
from auth import hash_password
from gap_engine import ROLE_BENCHMARKS


def seed_database(db: Session):
    # 1. Seed default Admin account if missing
    admin_email = "admin@careerx.ai"
    if not db.query(User).filter(User.email == admin_email).first():
        admin = User(
            full_name="CareerX Admin",
            email=admin_email,
            password_hash=hash_password("Admin@123"),
            role="admin",
        )
        db.add(admin)
        db.flush()
        db.add(StudentProfile(user_id=admin.id, target_role="AI/ML Engineer"))

    # 2. Seed all 9 Job Roles & Requirements
    role_details = {
        "Data Analyst": {
            "desc": "Transform raw operational datasets into executive KPI dashboards, SQL cohorts, and business decisions.",
            "resp": ["Write complex SQL queries & joins", "Clean & analyze data with Python/Excel", "Build interactive Power BI dashboards"],
            "tools": ["Excel", "SQL", "Python (Pandas)", "Power BI"],
            "pref": ["A/B Testing", "Storytelling", "ETL Basics"],
        },
        "Data Scientist": {
            "desc": "Build predictive statistical and machine learning models to forecast churn, demand, and risk.",
            "resp": ["Feature engineering & statistical validation", "Train & tune ML models", "Deploy predictive scoring pipelines"],
            "tools": ["Python", "Scikit-learn", "SQL", "Jupyter", "Statsmodels"],
            "pref": ["Deep Learning", "MLflow", "Cloud ML"],
        },
        "AI/ML Engineer": {
            "desc": "Architect, fine-tune, and deploy production LLM, NLP, and deep learning systems via scalable APIs.",
            "resp": ["Build RAG & LLM inference pipelines", "Optimize model latency & evaluation", "Deploy FastAPI/Docker ML services"],
            "tools": ["Python", "PyTorch", "Gemini / LLM APIs", "FastAPI", "Vector DBs"],
            "pref": ["Kubernetes", "Fine-tuning (LoRA)", "Evaluation Harnesses"],
        },
        "Software Developer": {
            "desc": "Design, test, and ship reliable software applications with clean data structures and modular architecture.",
            "resp": ["Implement core application logic", "Write unit & integration tests", "Collaborate via Git code reviews"],
            "tools": ["Python / Java / C++", "Git", "SQL", "REST APIs"],
            "pref": ["Docker", "System Design", "CI/CD"],
        },
        "Frontend Developer": {
            "desc": "Craft fast, accessible, responsive web interfaces connected to real-time backend APIs.",
            "resp": ["Build modular React/JS components", "Optimize Core Web Vitals & responsiveness", "Integrate REST/GraphQL endpoints"],
            "tools": ["HTML5", "CSS3", "JavaScript (ES6+)", "React.js"],
            "pref": ["TypeScript", "Tailwind CSS", "Chart.js"],
        },
        "Backend Developer": {
            "desc": "Build secure, high-throughput APIs, relational schemas, authentication flows, and cloud deployments.",
            "resp": ["Design normalized SQL schemas", "Implement JWT auth & rate limiting", "Deploy & monitor cloud services"],
            "tools": ["Python (FastAPI)", "PostgreSQL", "Docker", "Git"],
            "pref": ["Redis", "AWS / Render", "Message Queues"],
        },
        "Business Analyst": {
            "desc": "Bridge business stakeholders and engineering teams through KPI modeling, process mapping, and BI reporting.",
            "resp": ["Gather & document business requirements", "Analyze revenue & funnel metrics", "Present actionable recommendations"],
            "tools": ["Excel", "SQL", "Power BI / Tableau", "Jira"],
            "pref": ["Financial Modeling", "Agile Scrum", "Python Basics"],
        },
        "Cloud Engineer": {
            "desc": "Automate cloud infrastructure, container orchestration, CI/CD pipelines, and high-availability systems.",
            "resp": ["Provision cloud compute & storage", "Manage Docker & Kubernetes clusters", "Implement IAM security & monitoring"],
            "tools": ["Linux", "AWS / GCP", "Docker", "Terraform"],
            "pref": ["Kubernetes", "GitHub Actions", "Prometheus"],
        },
        "Cybersecurity Analyst": {
            "desc": "Monitor networks, audit application vulnerabilities, and respond to security incidents proactively.",
            "resp": ["Analyze SIEM alerts & traffic logs", "Conduct OWASP vulnerability scans", "Execute incident containment playbooks"],
            "tools": ["Linux", "Wireshark", "Nmap", "SIEM Tools", "Python"],
            "pref": ["Penetration Testing", "Cloud Security", "SOC Automation"],
        },
    }

    for title, meta in ROLE_BENCHMARKS.items():
        if not db.query(JobRole).filter(JobRole.title == title).first():
            info = role_details[title]
            jr = JobRole(
                title=title,
                description=info["desc"],
                responsibilities=info["resp"],
                tools=info["tools"],
                preferred_skills=info["pref"],
                readiness_threshold=75,
                recommended_projects=[meta["project"]],
                roadmap_steps=[f"Master {k} (>= {v}%)" for k, v in meta["skills"].items()],
            )
            db.add(jr)
            db.flush()
            for skill_name, req_score in meta["skills"].items():
                db.add(JobRequirement(role_id=jr.id, skill_name=skill_name, required_score=req_score))

    # 3. Seed Assessments & Questions
    if db.query(Assessment).count() == 0:
        sample_assessments = [
            (
                "Data Analyst",
                "Data Analyst Core Competency Assessment",
                [
                    ("SQL", "mcq", "Which SQL clause filters aggregated group results after GROUP BY?", ["WHERE", "HAVING", "ORDER BY", "DISTINCT"], "HAVING", "HAVING filters groups created by GROUP BY, whereas WHERE filters individual rows prior to grouping."),
                    ("SQL", "coding", "Write the SQL keyword used to return all rows from the left table and matched rows from the right table.", ["INNER JOIN", "LEFT JOIN", "CROSS JOIN", "UNION"], "LEFT JOIN", "LEFT JOIN preserves all records from the left table even when no match exists on the right."),
                    ("Python", "mcq", "In Pandas, which method removes rows containing missing (NaN) values?", ["df.fillna()", "df.dropna()", "df.isna()", "df.drop_duplicates()"], "df.dropna()", "df.dropna() drops missing values along the specified axis."),
                    ("Excel", "practical", "Which Excel function combines INDEX and MATCH superiority for modern two-way lookups?", ["VLOOKUP", "XLOOKUP", "CONCAT", "SUBTOTAL"], "XLOOKUP", "XLOOKUP supports left/right lookups, exact match by default, and built-in error fallback."),
                    ("Stats", "mcq", "When a dataset has extreme high outliers, which measure of central tendency is most robust?", ["Mean", "Median", "Range", "Variance"], "Median", "The median depends on rank order rather than magnitude, making it resistant to extreme outliers."),
                    ("Power BI", "practical", "In Power BI, which language is used to create calculated measures like YoY Revenue Growth?", ["M Query", "DAX", "SQL", "YAML"], "DAX", "Data Analysis Expressions (DAX) powers dynamic measures and time-intelligence calculations in Power BI."),
                ],
            ),
            (
                "AI/ML Engineer",
                "AI/ML & LLM Engineering Readiness Assessment",
                [
                    ("Python", "mcq", "Which Python feature allows FastAPI endpoints to handle concurrent I/O requests without blocking?", ["async / await", "lambda", "deepcopy", "yield from"], "async / await", "Asynchronous coroutines with async/await allow non-blocking I/O in ASGI servers like Uvicorn."),
                    ("Machine Learning", "mcq", "Which metric is best suited for evaluating a binary classifier on a heavily imbalanced fraud dataset?", ["Accuracy", "Precision-Recall AUC / F1", "MSE", "R-Squared"], "Precision-Recall AUC / F1", "Accuracy is misleading on imbalanced classes; F1 and PR-AUC focus on minority class performance."),
                    ("Deep Learning", "mcq", "What technique prevents overfitting in neural networks by randomly zeroing activations during training?", ["Batch Normalization", "Dropout", "Xavier Init", "Gradient Clipping"], "Dropout", "Dropout forces redundant representations by randomly deactivating neurons during training."),
                    ("LLM / NLP", "practical", "In a Retrieval-Augmented Generation (RAG) system, what is the primary role of vector embeddings?", ["Compress model weights", "Measure semantic similarity between query and documents", "Encrypt API keys", "Replace tokenizers"], "Measure semantic similarity between query and documents", "Embeddings map text into dense vector space so nearest-neighbor search retrieves semantically relevant context."),
                    ("SQL", "mcq", "Which index type speeds up exact-match lookups on a user email column in PostgreSQL?", ["B-Tree Index", "GIN Index", "BRIN Index", "Hash Join"], "B-Tree Index", "B-Tree is PostgreSQL's default and optimal index for equality and range queries."),
                ],
            ),
        ]

        for role_title, title, q_list in sample_assessments:
            a = Assessment(role_title=role_title, title=title, duration_minutes=15)
            db.add(a)
            db.flush()
            for skill_name, q_type, prompt, opts, ans, exp in q_list:
                db.add(
                    AssessmentQuestion(
                        assessment_id=a.id,
                        skill_name=skill_name,
                        question_type=q_type,
                        prompt=prompt,
                        options=opts,
                        correct_answer=ans,
                        explanation=exp,
                    )
                )

    # 4. Seed Learning Resources
    if db.query(LearningResource).count() == 0:
        resources = [
            ("SQL", "Advanced SQL for Analytics: Window Functions & CTEs", "Mode Analytics", "Interactive Lab", "https://mode.com/sql-tutorial/", 6),
            ("Power BI", "Power BI Data Modeling & DAX Mastery", "Microsoft Learn", "Guided Path", "https://learn.microsoft.com/en-us/training/powerplatform/power-bi", 8),
            ("Python", "Data Manipulation with Pandas & NumPy", "Kaggle Learn", "Hands-On Course", "https://www.kaggle.com/learn/pandas", 5),
            ("Stats", "Practical Statistics for Data Scientists", "StatQuest / OpenIntro", "Video + Exercises", "https://www.openintro.org/book/os/", 7),
            ("Machine Learning", "Applied Machine Learning Pipelines with Scikit-Learn", "Kaggle Learn", "Hands-On Course", "https://www.kaggle.com/learn/intro-to-machine-learning", 8),
            ("LLM / NLP", "Building Production RAG & Gemini API Applications", "Google AI for Developers", "Documentation & Lab", "https://ai.google.dev/gemini-api/docs", 6),
        ]
        for skill, title, provider, rtype, url, hrs in resources:
            db.add(LearningResource(skill_name=skill, title=title, provider=provider, resource_type=rtype, url=url, estimated_hours=hrs))

    # 5. Seed Projects
    if db.query(Project).count() == 0:
        projects = [
            Project(
                role_title="Data Analyst",
                title="Sales & Customer Churn Analytics Dashboard",
                description="Analyze 12 months of B2B SaaS subscription transactions to uncover churn drivers, cohort retention, and regional revenue trends.",
                technologies=["SQL", "Python (Pandas)", "Power BI", "Excel"],
                skills_developed=["SQL", "Power BI", "Stats", "Python"],
                difficulty="Intermediate",
                expected_outcome="Interactive 3-page executive dashboard + SQL cohort script + 5 actionable retention recommendations.",
                roadmap=["Clean raw CSV/SQL tables", "Write cohort retention queries", "Build DAX KPI cards in Power BI", "Publish executive summary"],
            ),
            Project(
                role_title="AI/ML Engineer",
                title="Enterprise Policy RAG & Skill Intelligence Assistant",
                description="Build a FastAPI + Gemini LLM document assistant with citation grounding, structured JSON extraction, and latency logging.",
                technologies=["Python", "FastAPI", "Gemini API", "Vector Embeddings"],
                skills_developed=["Python", "LLM / NLP", "Machine Learning"],
                difficulty="Intermediate",
                expected_outcome="Deployed REST API capable of answering domain queries with verifiable source citations.",
                roadmap=["Chunk & embed reference documents", "Implement semantic retrieval", "Connect Gemini structured JSON output", "Deploy & benchmark latency"],
            ),
            Project(
                role_title="Backend Developer",
                title="Multi-Tenant REST API with JWT Auth & Rate Limiting",
                description="Architect a production FastAPI + PostgreSQL backend with role-based permissions, migrations, and automated pytest coverage.",
                technologies=["Python", "FastAPI", "PostgreSQL", "JWT"],
                skills_developed=["Python / Node", "REST APIs", "SQL & PostgreSQL", "Auth & Security"],
                difficulty="Intermediate",
                expected_outcome="Live API with OpenAPI docs, role guards, and persistent relational storage.",
                roadmap=["Design normalized ER schema", "Implement PBKDF2/bcrypt + JWT", "Add rate limiting middleware", "Deploy to cloud"],
            ),
        ]
        db.add_all(projects)

    # 6. Seed Career Experience Simulation Modules
    if db.query(ExperienceModule).count() == 0:
        modules = [
            ExperienceModule(
                role_title="Data Analyst",
                title="Q3 Retail Revenue Drop Investigation (Simulated Workplace Assignment)",
                simulation_badge="Simulated Industry Experience (Not an Actual Company Internship)",
                scenario="You are a Junior Data Analyst at NovaCart Retail. Leadership noticed Q3 net revenue dropped 11% despite steady website traffic. Inspect the dataset below and diagnose the root cause.",
                sample_dataset=[
                    {"month": "July", "region": "North", "orders": 4200, "avg_order_value": 1850, "return_rate_pct": 4.2},
                    {"month": "August", "region": "North", "orders": 4150, "avg_order_value": 1620, "return_rate_pct": 8.9},
                    {"month": "September", "region": "North", "orders": 4090, "avg_order_value": 1490, "return_rate_pct": 12.4},
                ],
                tasks=[
                    "Calculate the percentage drop in Average Order Value (AOV) between July and September.",
                    "Identify the operational metric driving net revenue loss despite stable order volume (~4,100 orders).",
                    "Recommend 2 SQL/BI tracking metrics for the operations team.",
                ],
                deliverable_prompt="Write your root-cause diagnosis and 2 recommended KPIs based on the dataset above:",
            ),
            ExperienceModule(
                role_title="AI/ML Engineer",
                title="LLM Hallucination & Latency Triage Lab (Simulated Workplace Assignment)",
                simulation_badge="Simulated Industry Experience (Not an Actual Company Internship)",
                scenario="Your team's customer-support RAG bot has a 14% hallucination rate when users ask about refund deadlines, and p95 latency is 4.8 seconds.",
                sample_dataset=[
                    {"chunk_size": 1800, "top_k": 10, "hallucination_rate": "14%", "p95_latency_sec": 4.8},
                    {"chunk_size": 500, "top_k": 3, "hallucination_rate": "3%", "p95_latency_sec": 1.4},
                ],
                tasks=[
                    "Compare both retrieval configurations and explain why smaller chunks + lower top_k reduced hallucinations.",
                    "Propose a system prompt guardrail when retrieved context lacks the answer.",
                ],
                deliverable_prompt="Submit your engineering recommendation and fallback guardrail rule:",
            ),
        ]
        db.add_all(modules)

    db.commit()