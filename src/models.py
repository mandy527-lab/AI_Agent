from typing import Literal

from pydantic import BaseModel, Field


class MatchedRequirement(BaseModel):
    requirement: str = Field(description="職缺中的一項條件")
    resume_evidence: str = Field(description="履歷中支持此條件的原文證據")


class MissingRequirement(BaseModel):
    requirement: str = Field(description="履歷沒有證明的職缺條件")
    importance: Literal["必要", "加分", "不明"]
    action: str = Field(description="誠實且可執行的補強方式")


class InterviewQuestion(BaseModel):
    question: str
    reason: str = Field(description="這題與職缺或履歷的關係")
    answer_guide: str = Field(description="回答架構，不可替使用者虛構答案")


class JobFitAnalysis(BaseModel):
    role_title: str = Field(description="從職缺推測的職稱")
    match_score: int = Field(ge=0, le=100)
    summary: str
    matched_requirements: list[MatchedRequirement]
    missing_requirements: list[MissingRequirement]
    resume_suggestions: list[str]
    interview_questions: list[InterviewQuestion]

