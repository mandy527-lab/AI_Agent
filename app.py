import os

import streamlit as st
from dotenv import load_dotenv

from src.agent import analyze_job_fit
from src.resume_parser import extract_resume_text


load_dotenv()

st.set_page_config(
    page_title="JobFit Agent",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 JobFit Agent")
st.caption("用履歷中的真實證據分析職缺匹配度，不替你捏造經歷。")

with st.sidebar:
    st.header("使用說明")
    st.markdown(
        """
1. 上傳履歷
2. 貼上完整職缺內容
3. 點擊「開始分析」

你的履歷文字只會送到 Gemini API 進行本次分析。
請勿上傳不希望交給第三方處理的敏感資料。
"""
    )
    model = st.text_input(
        "Gemini 模型",
        value=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        help="可在 .env 內修改 GEMINI_MODEL。",
    )

resume_file = st.file_uploader(
    "1. 上傳履歷",
    type=["pdf", "docx", "txt"],
    help="支援文字型 PDF、Word 與純文字檔。",
)
job_description = st.text_area(
    "2. 貼上職缺內容",
    height=300,
    placeholder="請貼上職稱、工作內容、必要條件與加分條件……",
)

if st.button("開始分析", type="primary", use_container_width=True):
    if not os.getenv("GEMINI_API_KEY"):
        st.error("找不到 GEMINI_API_KEY。請依 README 建立 .env 檔案。")
    elif resume_file is None:
        st.warning("請先上傳履歷。")
    elif not job_description.strip():
        st.warning("請貼上職缺內容。")
    else:
        try:
            resume_text = extract_resume_text(resume_file)
            if not resume_text.strip():
                st.error("沒有讀到履歷文字。掃描版 PDF 請先轉成可選取文字的 PDF。")
                st.stop()

            with st.spinner("Agent 正在比對履歷與職缺……"):
                result = analyze_job_fit(
                    resume_text=resume_text,
                    job_description=job_description,
                    model=model,
                )

            st.success("分析完成")

            score_col, title_col = st.columns([1, 3])
            with score_col:
                st.metric("匹配分數", f"{result.match_score}/100")
            with title_col:
                st.subheader(result.role_title)
                st.write(result.summary)

            tab1, tab2, tab3, tab4 = st.tabs(
                ["符合條件", "技能缺口", "履歷建議", "面試準備"]
            )

            with tab1:
                if result.matched_requirements:
                    for item in result.matched_requirements:
                        st.markdown(f"**{item.requirement}**")
                        st.write(f"履歷證據：{item.resume_evidence}")
                else:
                    st.info("目前沒有找到明確符合的條件。")

            with tab2:
                if result.missing_requirements:
                    for item in result.missing_requirements:
                        st.markdown(f"**{item.requirement}**")
                        st.write(f"重要程度：{item.importance}")
                        st.write(f"下一步：{item.action}")
                else:
                    st.info("沒有發現明顯缺口。")

            with tab3:
                for suggestion in result.resume_suggestions:
                    st.markdown(f"- {suggestion}")
                st.warning("修改時只能使用你確實做過的經歷與成果。")

            with tab4:
                for index, question in enumerate(result.interview_questions, start=1):
                    st.markdown(f"**{index}. {question.question}**")
                    st.write(f"為什麼會問：{question.reason}")
                    st.write(f"回答方向：{question.answer_guide}")
                    st.divider()

        except ValueError as error:
            st.error(str(error))
        except Exception as error:
            st.error(f"分析失敗：{error}")
            st.info("請確認 Gemini API Key、免費額度、網路連線與模型名稱。")
