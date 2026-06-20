import os
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.agent import analyze_job_market
from src.examples import EXAMPLE_JOBS
from src.history import (
    analysis_from_entry,
    delete_history_entry,
    load_history,
    save_analysis,
)
from src.report import build_markdown_report
from src.resume_parser import extract_resume_text


load_dotenv()

st.set_page_config(
    page_title="Job Market Intelligence Agent",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
<style>
.block-container {max-width: 1180px; padding-top: 2rem;}
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #f8fafc, #eef2ff);
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 14px;
}
.evidence-box {
    border-left: 4px solid #6366f1;
    background: #f8fafc;
    border-radius: 0 10px 10px 0;
    padding: 10px 14px;
    margin: 8px 0;
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


def format_history_time(value: str) -> str:
    try:
        return datetime.fromisoformat(value).astimezone().strftime("%m/%d %H:%M")
    except (TypeError, ValueError):
        return "未知時間"


st.title("📊 Job Market Intelligence Agent")
st.caption("把零散職缺變成可追溯的市場情報，再排出你的學習與作品集優先順序。")

with st.sidebar:
    st.header("分析控制台")
    model = st.text_input(
        "Gemini 模型",
        value=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        help="可在 .env 內修改 GEMINI_MODEL。",
    )
    st.caption("資料會送到 Gemini API。免費方案請避免上傳敏感個資。")

    st.divider()
    st.subheader("快速開始")
    example_col, clear_col = st.columns(2)
    example_col.button("載入範例", on_click=load_examples, use_container_width=True)
    clear_col.button("清除職缺", on_click=clear_jobs, use_container_width=True)

    st.divider()
    st.subheader("分析紀錄")
    history = load_history()
    if history:
        history_labels = {
            (
                f"{item.get('target_role', '未命名')} · "
                f"{format_history_time(item.get('created_at', ''))}"
            ): item
            for item in history
        }
        selected_label = st.selectbox("最近 20 次", list(history_labels))
        selected_entry = history_labels[selected_label]
        load_col, delete_col = st.columns(2)
        if load_col.button("載入", use_container_width=True):
            st.session_state["market_result"] = analysis_from_entry(selected_entry)
            st.session_state["used_resume"] = selected_entry.get(
                "used_resume", False
            )
            st.rerun()
        if delete_col.button("刪除", use_container_width=True):
            delete_history_entry(selected_entry["id"])
            st.rerun()
        st.caption("僅保存分析結果，不保存履歷或完整職缺原文。")
    else:
        st.caption("完成第一次分析後，紀錄會保存在本機。")

st.subheader("1. 收集要比較的職缺")
job_count = st.number_input(
    "職缺數量",
    min_value=2,
    max_value=5,
    value=3,
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

st.subheader("2. 選擇性加入履歷")
st.write("不放履歷也能分析市場；放入後才會判斷你的優勢與技能缺口。")
resume_file = st.file_uploader(
    "上傳履歷（選填）",
    type=["pdf", "docx", "txt"],
    help="支援文字型 PDF、Word 與純文字檔。",
)

if st.button("開始市場分析", type="primary", use_container_width=True):
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

            with st.spinner("Agent 正在整理需求、核對證據與建立行動計畫……"):
                result = analyze_job_market(
                    job_descriptions=job_descriptions,
                    resume_text=resume_text,
                    model=model,
                )

            st.session_state["market_result"] = result
            st.session_state["used_resume"] = bool(resume_text)
            save_analysis(result, used_resume=bool(resume_text))
        except ValueError as error:
            st.error(str(error))
        except Exception as error:
            st.error(f"分析失敗：{error}")
            st.info("請確認 Gemini API Key、免費額度、網路連線與模型名稱。")

if "market_result" in st.session_state:
    result = st.session_state["market_result"]
    used_resume = st.session_state.get("used_resume", False)

    st.divider()
    st.success("市場分析完成，結果已保存到本機紀錄。")
    role_col, jobs_col, skills_col, evidence_col = st.columns([2, 1, 1, 1])
    role_col.metric("目標職位", result.target_role)
    jobs_col.metric("分析職缺", result.total_jobs)
    skills_col.metric("技能類別", len(result.top_skills))
    evidence_col.metric(
        "原文證據",
        sum(len(skill.evidence) for skill in result.top_skills),
    )
    st.info(result.market_summary)

    report = build_markdown_report(result)
    st.download_button(
        "下載完整 Markdown 報告",
        data=report,
        file_name="job-market-analysis.md",
        mime="text/markdown",
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["市場總覽", "證據與職缺", "個人差距", "行動計畫"]
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
        st.caption("可回到來源職缺核對，降低 AI 分類錯誤帶來的風險。")
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
            st.info("這次沒有提供履歷，因此不對個人能力下判斷。")
        else:
            strength_col, gap_col = st.columns(2)
            with strength_col:
                st.subheader("已有優勢")
                if result.candidate_strengths:
                    for item in result.candidate_strengths:
                        with st.container(border=True):
                            st.markdown(f"**{item.skill}**")
                            st.write(f"履歷證據：{item.resume_evidence}")
                            st.caption(item.market_relevance)
                else:
                    st.write("沒有找到能明確連結市場需求的履歷證據。")

            with gap_col:
                st.subheader("技能缺口")
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
                st.success(f"能力證明：{step.proof_of_skill}")

        st.subheader("面試準備主題")
        for topic in result.interview_focus:
            st.markdown(f"- {topic}")
