import streamlit as st

# ==========================================
# 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="SDH ACADEMY 통합 출제 플랫폼", layout="wide")

st.title("SDH ACADEMY 통합 출제 플랫폼 🛠️")
st.markdown("---")

# ==========================================
# 메인 탭 구성
# ==========================================
tab_workbook, tab_exam = st.tabs(["📚 워크북 제작", "🎯 변형문제 제작"])

# ------------------------------------------
# 탭 1: 워크북 제작 (UI 뼈대)
# ------------------------------------------
with tab_workbook:
    st.subheader("📖 모의고사 워크북 제작")
    st.info("워크북 제작 기능은 준비 중입니다.")
    # 향후 워크북 관련 UI가 추가될 자리입니다.

# ------------------------------------------
# 탭 2: 내신 변형문제 제작 (UI 뼈대)
# ------------------------------------------
with tab_exam:
    st.subheader("🎯 1. 출제 범위 선택 (모의고사)")
    
    # 학년, 연도, 월 선택 드롭다운
    col1, col2, col3 = st.columns(3)
    with col1:
        st.selectbox("대상 학년", ["고1", "고2", "고3"])
    with col2:
        st.selectbox("모의고사 연도", ["2026년", "2025년", "2024년"])
    with col3:
        st.selectbox("시행 월", ["3월", "6월", "9월", "11월"])
        
    st.write("")
    
    # 지문 선택 체크박스
    st.checkbox("✅ 전체 지문 선택", key="select_all_q")
    
    q_cols = st.columns(10)
    for i, q_num in enumerate(range(18, 46)):
        with q_cols[i % 10]:
            st.checkbox(f"{q_num}번", key=f"q_{q_num}")

    st.markdown("---")
    
    st.subheader("🎯 2. 문제 유형 선택")
    
    # 문제 유형 선택 체크박스
    st.checkbox("✅ 전체 유형 선택", key="select_all_types")
    
    t_col1, t_col2, t_col3, t_col4 = st.columns(4)
    with t_col1:
        st.checkbox("어법 추론")
        st.checkbox("어휘 추론")
    with t_col2:
        st.checkbox("빈칸 추론")
        st.checkbox("함축 의미")
    with t_col3:
        st.checkbox("글의 순서")
        st.checkbox("문장 삽입")
    with t_col4:
        st.checkbox("서술형 영작")
        st.checkbox("주제/제목")

    st.markdown("---")
    
    # ------------------------------------------
    # 실행 버튼
    # ------------------------------------------
    if st.button("🚀 변형문제 생성 및 인쇄용 문서 다운로드", type="primary", use_container_width=True):
        # 향후 Gemini API 호출 및 HTML/PDF 문서 생성 로직이 들어갈 자리입니다.
        st.success("성공적으로 요청이 접수되었습니다! (여기에 API 연동 및 문서 생성 로직이 추가됩니다.)")

# ==========================================
# 하단 푸터
# ==========================================
st.markdown("---")
# 💥 수정 포인트: 1학기 교재명 삭제 및 시스템 이름으로 깔끔하게 변경
st.markdown("<div style='text-align: center; color: gray; font-size: 12px;'>SDH ACADEMY Internal Exam System</div>", unsafe_allow_html=True)
