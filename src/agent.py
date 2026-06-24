import os
import time
from typing import Any, Optional

from google import genai
from google.genai import errors

from src.models import MarketAnalysis


SYSTEM_PROMPT = """
你是一位謹慎的求職市場情報分析師。請使用繁體中文分析多個職缺。

任務：
1. 分別辨識每個職缺的職稱、公司與重要條件。
2. 將同義技能標準化後，統計它出現於幾個職缺。
3. 區分技能偏向必要條件、加分條件或兩者皆有。
4. 根據跨職缺出現頻率與重要性判斷需求程度。
5. 每個技能都必須附上來源職缺編號與支持判斷的原文短句，不可改寫成不存在的要求。
6. confidence 表示分類可信度；原文清楚寫明時為高，需語意推論時為中或低。
7. 若有履歷，只能把履歷明確出現的內容視為候選人的能力。
8. 若沒有履歷，candidate_strengths 與 skill_gaps 必須回傳空陣列，
   learning_plan 則提供一般性的市場準備順序。
9. 不可推測、誇大或捏造候選人的技能、年資、成果、公司或學歷。
10. 技能缺口必須是市場確實要求、但履歷沒有證據支持的能力。
11. 學習計畫要具體，並包含可以放進作品集的能力證明。
12. 這是市場分析與決策支援，不是履歷代寫服務。
""".strip()

RETRYABLE_STATUS_CODES = {500, 502, 503, 504}


class AnalysisTemporarilyUnavailableError(RuntimeError):
    """Raised when all configured Gemini models remain temporarily unavailable."""


def build_market_prompt(
    job_descriptions: list[str],
    resume_text: str = "",
) -> str:
    """Build a prompt with clearly separated jobs and optional resume evidence."""
    job_sections = "\n\n".join(
        f"<job number=\"{index}\">\n{description.strip()}\n</job>"
        for index, description in enumerate(job_descriptions, start=1)
    )
    resume_section = (
        f"<resume>\n{resume_text.strip()}\n</resume>"
        if resume_text.strip()
        else "<resume>未提供履歷，請只進行市場分析。</resume>"
    )

    return f"""
請分析以下 {len(job_descriptions)} 個職缺，找出共同需求與差異。

{job_sections}

{resume_section}
""".strip()


def analyze_job_market(
    job_descriptions: list[str],
    resume_text: str = "",
    model: str = "gemini-3.5-flash",
    client: Optional[Any] = None,
    fallback_model: Optional[str] = None,
    sleep: Any = time.sleep,
) -> MarketAnalysis:
    """Analyze two to five jobs and optionally compare them with a resume."""
    cleaned_jobs = [job.strip() for job in job_descriptions if job.strip()]
    if len(cleaned_jobs) < 2:
        raise ValueError("請至少提供 2 個完整職缺。")
    if len(cleaned_jobs) > 5:
        raise ValueError("第一版最多分析 5 個職缺。")

    gemini_client = client or genai.Client()
    fallback = fallback_model or os.getenv(
        "GEMINI_FALLBACK_MODEL",
        "gemini-3.1-flash-lite",
    )
    models = list(dict.fromkeys([model, fallback]))
    prompt = build_market_prompt(cleaned_jobs, resume_text)
    response = None
    last_error = None

    for candidate_model in models:
        for attempt, delay in enumerate((2, 4, None), start=1):
            try:
                response = gemini_client.models.generate_content(
                    model=candidate_model,
                    contents=prompt,
                    config={
                        "system_instruction": SYSTEM_PROMPT,
                        "response_mime_type": "application/json",
                        "response_schema": MarketAnalysis,
                    },
                )
                break
            except errors.ServerError as error:
                if error.code not in RETRYABLE_STATUS_CODES:
                    raise
                last_error = error
                if delay is not None:
                    sleep(delay)
        if response is not None:
            break

    if response is None:
        raise AnalysisTemporarilyUnavailableError(
            "Gemini 目前使用量較高，主模型與備援模型都暫時無法回應。"
        ) from last_error
    if not response.text:
        raise ValueError("模型沒有回傳可用的市場分析，請再試一次。")

    return MarketAnalysis.model_validate_json(response.text)
