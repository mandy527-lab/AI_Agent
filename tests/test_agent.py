from unittest.mock import Mock

import pytest

from src.agent import analyze_job_fit, build_user_prompt
from src.models import JobFitAnalysis


def test_build_user_prompt_separates_resume_and_job_description():
    prompt = build_user_prompt("Python developer", "Need Python")

    assert "<resume>" in prompt
    assert "Python developer" in prompt
    assert "<job_description>" in prompt
    assert "Need Python" in prompt


def test_analyze_job_fit_rejects_empty_resume():
    with pytest.raises(ValueError, match="履歷內容不能是空白"):
        analyze_job_fit("", "Need Python")


def test_analyze_job_fit_returns_parsed_result():
    expected = JobFitAnalysis(
        role_title="Python 工程師",
        match_score=80,
        summary="具備主要技能。",
        matched_requirements=[],
        missing_requirements=[],
        resume_suggestions=["把 Python 專案移到前面。"],
        interview_questions=[],
    )
    fake_client = Mock()
    fake_client.models.generate_content.return_value.text = expected.model_dump_json()

    result = analyze_job_fit(
        "I use Python.",
        "We need Python.",
        client=fake_client,
    )

    assert result == expected
    fake_client.models.generate_content.assert_called_once()
