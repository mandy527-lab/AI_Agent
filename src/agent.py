from typing import Any, Optional

from google import genai

from src.models import JobFitAnalysis


SYSTEM_PROMPT = """
你是一位謹慎、誠實的求職策略顧問。請使用繁體中文分析履歷與職缺。

規則：
1. 只能把履歷明確出現的內容視為候選人的經驗。
2. 不可推測、誇大或捏造技能、年資、職稱、成果、公司或學歷。
3. 每個「符合條件」都必須附上履歷中的具體證據；沒有證據就放入缺口。
4. 匹配分數需考慮必要條件、加分條件與證據強度，不可只比對關鍵字。
5. 履歷建議可以改善措辭與排序，但不得加入不存在的經歷或數字。
6. 面試回答方向只能提供架構，不能替候選人編造故事。
7. 若職缺資訊不足，請保守評分並明確反映不確定性。
""".strip()


def build_user_prompt(resume_text: str, job_description: str) -> str:
    """Build a clearly separated prompt to reduce instruction confusion."""
    return f"""
請分析以下資料。

<resume>
{resume_text}
</resume>

<job_description>
{job_description}
</job_description>
""".strip()


def analyze_job_fit(
    resume_text: str,
    job_description: str,
    model: str = "gemini-3.5-flash",
    client: Optional[Any] = None,
) -> JobFitAnalysis:
    """Analyze resume-to-job fit and return validated structured data."""
    if not resume_text.strip():
        raise ValueError("履歷內容不能是空白。")
    if not job_description.strip():
        raise ValueError("職缺內容不能是空白。")

    gemini_client = client or genai.Client()
    response = gemini_client.models.generate_content(
        model=model,
        contents=build_user_prompt(resume_text, job_description),
        config={
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_schema": JobFitAnalysis,
        },
    )

    if not response.text:
        raise ValueError("模型沒有回傳可用的分析結果，請再試一次。")

    return JobFitAnalysis.model_validate_json(response.text)
