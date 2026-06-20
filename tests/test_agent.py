from unittest.mock import Mock

import pytest

from src.agent import analyze_job_market, build_market_prompt
from src.models import MarketAnalysis


def sample_analysis() -> MarketAnalysis:
    return MarketAnalysis(
        target_role="資料分析師",
        total_jobs=2,
        market_summary="SQL 與資料視覺化是共同需求。",
        job_summaries=[
            {
                "job_number": 1,
                "role_title": "Data Analyst",
                "company": "A 公司",
                "key_requirements": ["SQL"],
            },
            {
                "job_number": 2,
                "role_title": "Data Analyst",
                "company": "B 公司",
                "key_requirements": ["SQL", "Tableau"],
            },
        ],
        top_skills=[
            {
                "skill": "SQL",
                "demand_count": 2,
                "demand_level": "高",
                "requirement_type": "必要為主",
                "source_jobs": [1, 2],
                "confidence": "高",
                "evidence": [
                    {"job_number": 1, "quote": "熟悉 SQL"},
                    {"job_number": 2, "quote": "撰寫 SQL 查詢"},
                ],
            }
        ],
        candidate_strengths=[],
        skill_gaps=[],
        learning_plan=[
            {
                "order": 1,
                "focus": "SQL",
                "action": "完成查詢練習。",
                "proof_of_skill": "公開 SQL 分析專案。",
            }
        ],
        interview_focus=["SQL 查詢思路"],
    )


def test_build_market_prompt_separates_jobs_and_optional_resume():
    prompt = build_market_prompt(
        ["Need Python", "Need SQL"],
        "Python developer",
    )

    assert '<job number="1">' in prompt
    assert '<job number="2">' in prompt
    assert "<resume>" in prompt
    assert "Python developer" in prompt


def test_build_market_prompt_handles_missing_resume():
    prompt = build_market_prompt(["Job A", "Job B"])

    assert "未提供履歷" in prompt


def test_analyze_job_market_requires_two_jobs():
    with pytest.raises(ValueError, match="至少提供 2 個"):
        analyze_job_market(["Only one job"])


def test_analyze_job_market_rejects_more_than_five_jobs():
    with pytest.raises(ValueError, match="最多分析 5 個"):
        analyze_job_market([f"Job {index}" for index in range(6)])


def test_analyze_job_market_returns_validated_result():
    expected = sample_analysis()
    fake_client = Mock()
    fake_client.models.generate_content.return_value.text = expected.model_dump_json()

    result = analyze_job_market(
        ["Need SQL", "Need SQL and Tableau"],
        client=fake_client,
    )

    assert result == expected
    fake_client.models.generate_content.assert_called_once()
