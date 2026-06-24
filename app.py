import os
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.agent import AnalysisTemporarilyUnavailableError, analyze_job_market
from src.examples import EXAMPLE_JOBS
from src.history import (
    analysis_from_entry,
    create_history_entry,
)
from src.report import build_markdown_report
from src.resume_parser import extract_resume_text


load_dotenv()


def load_cloud_secrets() -> None:
    """Expose Streamlit Cloud secrets to SDKs that read environment variables."""
    try:
        for key in ("GEMINI_API_KEY", "GEMINI_MODEL"):
            if key in st.secrets and not os.getenv(key):
                os.environ[key] = str(st.secrets[key])
    except FileNotFoundError:
        pass


load_cloud_secrets()

st.set_page_config(
    page_title="職缺市場分析",
    page_icon=":material/query_stats:",
    layout="wide",
)

st.markdown(
    """
<style>
[data-testid="stAppViewContainer"] {
    background: #f6f8fc;
}
[data-testid="stHeader"] {
    display: block;
    background: transparent;
}
[data-testid="stDecoration"] {
    display: none;
}
.block-container {
    max-width: 1180px;
    padding-top: 1.5rem;
    padding-bottom: 4rem;
}
[data-testid="stSidebar"] {
    background: #eef3f8;
    border-right: 1px solid #dfe6ee;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.75rem;
}
[data-testid="stMetric"] {
    background: #eaf2ff;
    border: 1px solid #d6e5fb;
    border-radius: 8px;
    padding: 12px 14px;
}
[data-baseweb="tab-list"] {
    background: #edf2f7;
    border-radius: 8px;
    padding: 4px;
}
[data-testid="stExpander"] {
    background: #ffffff;
    border-color: #dfe6ee;
}
.hero-panel {
    background: #e8f1fb;
    border: 1px solid #d3e2f2;
    border-radius: 10px;
    padding: 22px;
    overflow: visible;
}
.hero-title {
    color: #172033;
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.35;
    letter-spacing: -0.025em;
    padding-top: 2px;
}
.hero-copy {
    color: #526177;
    font-size: 0.92rem;
    margin-top: 7px;
}
.evidence-box {
    border-left: 3px solid #64748b;
    background: #f8fafc;
    border-radius: 0 6px 6px 0;
    padding: 10px 12px;
    margin: 8px 0;
}
.product-name {
    font-size: 1.05rem;
    font-weight: 650;
    letter-spacing: -0.01em;
    color: #111827;
}
.product-label {
    margin-top: 2px;
    font-size: 0.78rem;
    color: #6b7280;
}
.section-label {
    margin-top: 8px;
    margin-bottom: -2px;
    font-size: 0.72rem;
    font-weight: 650;
    letter-spacing: 0.08em;
    color: #6b7280;
    text-transform: uppercase;
}
.result-summary {
    background: #edf7f5;
    border: 1px solid #d1ebe5;
    border-radius: 8px;
    padding: 14px 16px;
    color: #374151;
    margin: 10px 0 16px;
}
</style>
""",
    unsafe_allow_html=True,
)


def load_examples() -> None:
    st.session_state["job_count"] = len(EXAMPLE_JOBS)
    for index, job in enumerate(EXAMPLE_JOBS):
        st.session_state[f"job_{index}"] = job


def clear_jobs() -> None:
    for index in range(5):
        st.session_state[f"job_{index}"] = ""
    st.session_state.pop("market_result", None)
    st.session_state.pop("used_resume", None)
    st.session_state.pop("resume_file", None)


def format_history_time(value: str) -> str:
    try:
        return datetime.fromisoformat(value).astimezone().strftime("%m/%d %H:%M")
    except (TypeError, ValueError):
        return "未知時間"


model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
history = st.session_state.setdefault("analysis_history", [])
st.session_state.setdefault("job_count", 3)

with st.sidebar:
    st.subheader("分析紀錄")
    if history:
        for entry in history[:10]:
            label = (
                f"{entry.get('target_role', '未命名')}\n"
                f"{format_history_time(entry.get('created_at', ''))}"
            )
            if st.button(
                label,
                key=f"history_{entry['id']}",
                use_container_width=True,
                help=f"{entry.get('total_jobs', 0)} 個職缺"
                f" · {'含履歷比對' if entry.get('used_resume') else '市場分析'}",
            ):
                st.session_state["market_result"] = analysis_from_entry(entry)
                st.session_state["used_resume"] = entry.get("used_resume", False)
                st.rerun()
    else:
        st.caption("尚無分析紀錄")

    st.divider()
    st.caption("分析模型")
    st.code(model, language=None)

title_col, action_col = st.columns([3, 2], vertical_alignment="center")
with title_col:
    st.markdown(
        """
<div class="hero-panel">
    <div class="hero-title">職缺市場分析</div>
    <div class="hero-copy">
        比較多個相似職缺，整理共同需求、原文證據與準備優先順序。
    </div>
</div>
""",
        unsafe_allow_html=True,
    )
with action_col:
    example_col, clear_col = st.columns(2)
    example_col.button(
        "點我看範例",
        on_click=load_examples,
        use_container_width=True,
        icon=":material/preview:",
    )
    clear_col.button(
        "清除職缺",
        on_click=clear_jobs,
        use_container_width=True,
        icon=":material/delete_sweep:",
    )

st.subheader("職缺資料")
st.caption("建議放入 2–5 個相近職位，讓比較結果更有參考價值。")
job_count = st.number_input(
    "職缺數量",
    min_value=2,
    max_value=5,
    step=1,
    key="job_count",
    help="建議選擇相似職位，才能看出有意義的共同需求。",
)

job_descriptions = []
for index in range(int(job_count)):
    with st.expander(f"職缺 {index + 1}", expanded=index < 2):
        job_descriptions.append(
            st.text_area(
                "完整職缺內容",
                height=190,
                key=f"job_{index}",
                label_visibility="collapsed",
                placeholder="貼上公司、職稱、工作內容、必要條件與加分條件……",
            )
        )

with st.expander("加入履歷比對（選填）"):
    st.caption("未上傳時只分析市場；上傳後會額外整理已有優勢與技能缺口。")
    resume_file = st.file_uploader(
        "履歷檔案",
        type=["pdf", "docx", "txt"],
        key="resume_file",
        help="支援文字型 PDF、Word 與純文字檔。",
    )

if st.button(
    "產生分析",
    type="primary",
    use_container_width=True,
    icon=":material/analytics:",
):
    if not os.getenv("GEMINI_API_KEY"):
        st.error("找不到 GEMINI_API_KEY。請依 README 設定 .env。")
    elif sum(bool(job.strip()) for job in job_descriptions) < 2:
        st.warning("請至少貼上 2 個完整職缺。")
    else:
        try:
            resume_text = ""
            if resume_file is not None:
                resume_text = extract_resume_text(resume_file)
                if not resume_text.strip():
                    st.error("沒有讀到履歷文字。掃描版 PDF 請先進行 OCR。")
                    st.stop()

            with st.spinner("正在整理職缺需求與原文證據……"):
                result = analyze_job_market(
                    job_descriptions=job_descriptions,
                    resume_text=resume_text,
                    model=model,
                )

            st.session_state["market_result"] = result
            st.session_state["used_resume"] = bool(resume_text)
            history.insert(0, create_history_entry(result, bool(resume_text)))
            del history[20:]
        except AnalysisTemporarilyUnavailableError:
            st.error("分析服務目前使用量較高，請稍候 1–2 分鐘再試一次。")
            st.caption("系統已自動重試，並嘗試切換備援模型。")
        except ValueError as error:
            st.error(str(error))
        except Exception as error:
            st.error(f"分析失敗：{error}")
            st.info("請確認 Gemini API Key、免費額度、網路連線與模型名稱。")

if "market_result" in st.session_state:
    result = st.session_state["market_result"]
    used_resume = st.session_state.get("used_resume", False)

    st.divider()
    st.header("分析結果")
    st.caption("分析完成 · 已保存至本機紀錄")
    st.caption("目標職位")
    st.subheader(result.target_role)
    jobs_col, skills_col, evidence_col = st.columns(3)
    jobs_col.metric("分析職缺", result.total_jobs)
    skills_col.metric("技能類別", len(result.top_skills))
    evidence_col.metric(
        "原文證據",
        sum(len(skill.evidence) for skill in result.top_skills),
    )
    st.markdown(
        f'<div class="result-summary">{result.market_summary}</div>',
        unsafe_allow_html=True,
    )

    report = build_markdown_report(result)
    st.download_button(
        "下載分析報告",
        data=report,
        file_name="job-market-analysis.md",
        mime="text/markdown",
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["市場職缺總覽", "各項職缺分析證據", "個人能力分析", "行動計畫"]
    )

    with tab1:
        skill_rows = [
            {
                "技能": item.skill,
                "出現職缺數": item.demand_count,
                "需求程度": item.demand_level,
                "條件類型": item.requirement_type,
                "判斷信心": item.confidence,
            }
            for item in result.top_skills
        ]
        skill_df = pd.DataFrame(skill_rows)
        if not skill_df.empty:
            chart_col, type_col = st.columns([3, 2])
            with chart_col:
                st.subheader("技能需求排行")
                demand_chart = (
                    alt.Chart(skill_df)
                    .mark_bar(cornerRadiusEnd=6)
                    .encode(
                        x=alt.X("出現職缺數:Q", title="出現職缺數"),
                        y=alt.Y("技能:N", sort="-x", title=None),
                        color=alt.Color(
                            "需求程度:N",
                            scale=alt.Scale(
                                domain=["高", "中", "低"],
                                range=["#ef4444", "#f59e0b", "#10b981"],
                            ),
                        ),
                        tooltip=list(skill_df.columns),
                    )
                    .properties(height=max(260, len(skill_df) * 32))
                )
                st.altair_chart(demand_chart, use_container_width=True)

            with type_col:
                st.subheader("條件類型分布")
                type_df = (
                    skill_df.groupby("條件類型")
                    .size()
                    .reset_index(name="技能數")
                )
                type_chart = (
                    alt.Chart(type_df)
                    .mark_arc(innerRadius=55)
                    .encode(
                        theta=alt.Theta("技能數:Q"),
                        color=alt.Color(
                            "條件類型:N",
                            scale=alt.Scale(
                                range=["#4f46e5", "#06b6d4", "#8b5cf6", "#94a3b8"]
                            ),
                        ),
                        tooltip=["條件類型", "技能數"],
                    )
                    .properties(height=280)
                )
                st.altair_chart(type_chart, use_container_width=True)

            st.dataframe(
                skill_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "出現職缺數": st.column_config.ProgressColumn(
                        "出現職缺數",
                        min_value=0,
                        max_value=result.total_jobs,
                        format="%d",
                    )
                },
            )

    with tab2:
        st.subheader("技能判斷的原文證據")
        st.caption("每項判斷都可回到來源職缺核對。")
        for skill in result.top_skills:
            with st.expander(
                f"{skill.skill}｜{skill.demand_count}/{result.total_jobs} 個職缺"
                f"｜信心 {skill.confidence}",
                expanded=skill.demand_level == "高",
            ):
                for evidence in skill.evidence:
                    st.markdown(
                        f'<div class="evidence-box"><b>職缺 '
                        f"{evidence.job_number}</b><br>「{evidence.quote}」</div>",
                        unsafe_allow_html=True,
                    )

        st.subheader("逐一比較職缺")
        for job in result.job_summaries:
            with st.expander(
                f"職缺 {job.job_number}｜{job.company}｜{job.role_title}"
            ):
                for requirement in job.key_requirements:
                    st.markdown(f"- {requirement}")

    with tab3:
        if not used_resume:
            st.info("這次沒有提供履歷，因此無法整理個人優勢與待補強能力。")
        else:
            st.caption("根據履歷中的明確證據，比對市場需求後整理優勢與待補強項目。")
            strength_col, gap_col = st.columns(2)
            with strength_col:
                st.subheader("個人優勢")
                if result.candidate_strengths:
                    for item in result.candidate_strengths:
                        with st.container(border=True):
                            st.markdown(f"**{item.skill}**")
                            st.write(f"履歷證據：{item.resume_evidence}")
                            st.caption(item.market_relevance)
                else:
                    st.write("沒有找到能明確連結市場需求的履歷證據。")

            with gap_col:
                st.subheader("待補強能力")
                if result.skill_gaps:
                    for item in result.skill_gaps:
                        with st.container(border=True):
                            st.markdown(f"**{item.skill}｜{item.priority}優先**")
                            st.write(item.reason)
                            st.caption(f"下一步：{item.next_step}")
                else:
                    st.write("沒有發現明顯技能缺口。")

    with tab4:
        st.subheader("學習與作品集順序")
        for step in sorted(result.learning_plan, key=lambda item: item.order):
            with st.container(border=True):
                st.markdown(f"### {step.order}. {step.focus}")
                st.write(step.action)
                st.caption(f"建議產出：{step.proof_of_skill}")

        st.subheader("面試準備主題")
        for topic in result.interview_focus:
            st.markdown(f"- {topic}")
