import os
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gap_engine import analyze_skill_gap, ROLE_BENCHMARKS

app = FastAPI(title="CareerX API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SkillInput(BaseModel):
    target_role: str
    demonstrated_skills: Dict[str, int]


@app.get("/")
def home():
    return {"status": "CareerX backend chal raha hai!"}


@app.get("/roles")
def list_roles():
    return {"roles": list(ROLE_BENCHMARKS.keys())}


@app.post("/analyze")
def analyze(data: SkillInput):
    try:
        return analyze_skill_gap(data.target_role, data.demonstrated_skills)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)