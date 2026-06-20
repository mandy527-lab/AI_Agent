from typing import Literal

from pydantic import BaseModel, Field


class JobSummary(BaseModel):
    job_number: int = Field(ge=1, description="職缺在輸入中的編號")
    role_title: str = Field(description="職稱")
    company: str = Field(description="公司名稱；未提供時填寫「未提供」")
    key_requirements: list[str] = Field(description="此職缺最重要的條件")


class SkillDemand(BaseModel):
    skill: str = Field(description="標準化後的技能名稱")
    demand_count: int = Field(ge=1, description="提到此技能的職缺數")
    demand_level: Literal["高", "中", "低"]
    requirement_type: Literal["必要為主", "加分為主", "混合", "不明"]
    source_jobs: list[int] = Field(description="提到此技能的職缺編號")


class CandidateStrength(BaseModel):
    skill: str
    resume_evidence: str = Field(description="履歷中的具體證據")
    market_relevance: str = Field(description="此能力與市場需求的關係")


class SkillGap(BaseModel):
    skill: str
    demand_count: int = Field(ge=1)
    priority: Literal["高", "中", "低"]
    reason: str
    next_step: str = Field(description="具體、誠實且可執行的補強方式")


class LearningStep(BaseModel):
    order: int = Field(ge=1)
    focus: str
    action: str
    proof_of_skill: str = Field(description="可用來證明能力的作品或成果")


class MarketAnalysis(BaseModel):
    target_role: str = Field(description="這批職缺代表的目標職位")
    total_jobs: int = Field(ge=2, le=5)
    market_summary: str
    job_summaries: list[JobSummary]
    top_skills: list[SkillDemand]
    candidate_strengths: list[CandidateStrength]
    skill_gaps: list[SkillGap]
    learning_plan: list[LearningStep]
    interview_focus: list[str] = Field(description="這批職缺共同可能關注的面試主題")

