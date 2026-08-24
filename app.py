import streamlit as st
import pandas as pd

st.set_page_config(page_title="내신 출제 플랫폼", layout="wide")

# 타이틀 및 헤더
st.title("에스디에이치어학원 통합 출제 플랫폼 🛠️")
st.markdown("---")

# 1. 상단 탭(메뉴) 생성
tab_workbook, tab_exam = st.tabs(["📚 워크북 제작", "🎯 내신 변형문제 제작"])

# ==========================================
# 탭 1: 워크북 제작 화면 (PPT 1~3페이지 참고)
# ==========================================
with tab_workbook:
    st.subheader("📖 모의고사 워크북 검색 및 다운로드")
    
    # 학년/연도/월 필터 UI (가로 배치)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        grade = st.selectbox("학년", ["고1", "고2", "고3"], index=1) # 고2를 기본값으로 세팅
    with col2:
        year = st.selectbox("연도", ["2026년", "2025년", "2024년", "2023년"])
    with col3:
        month = st.selectbox("시행 월", ["3월", "6월", "9월", "11월"])
    with col4:
        st.write("") # 간격 맞추기
        search_btn = st.button("🔍 자료 검색", use_container_width=True)
        
    st.markdown("---")
    
    # 검색 버튼을 누르면 가상의 엑셀 리스트가 나타나도록 설정
    if search_btn:
        st.success(f"✅ {year} {month} {grade} 모의고사 워크북 목록을 불러왔습니다.")
        
        # 가상의 데이터 (향후 실제 DB와 연결될 부분)
        data = {
            "자료명": [
                f"{year} {month} {grade} 모의고사 10단계 WORKBOOK 통합본",
                f"{year} {month} {grade} 모의고사 WORKBOOK 1 지문연습",
                f"{year} {month} {grade} 모의고사 WORKBOOK 2 빈칸완성",
                f"{year} {month} {grade} 모의고사 WORKBOOK 3 해석연습",
                f"{year} {month} {grade} 모의고사 WORKBOOK 4 순서배열"
            ],
            "문항 수": [329, 45, 45, 45, 45],
            "업로드일": ["2026-08-25"] * 5
        }
        df = pd.DataFrame(data)
        
        # 맨 앞에 체크박스(선택) 열 추가
        df.insert(0, "선택", False)
        
        # 화면에 표 그리기 (체크박스 클릭 가능)
        edited_df = st.data_editor(
            df,
            column_config={
                "선택": st.column_config.CheckboxColumn("선택", default=False)
            },
            disabled=["자료명", "문항 수", "업로드일"], # 선택 칸 외에는 수정 불가
            hide_index=True,
            use_container_width=True
        )
        
        # 다운로드 버튼 세팅
        if st.button("📥 선택 파일 다운로드 (테스트)", type="primary"):
            st.info("선택하신 워크북 파일이 다운로드 되었습니다! (현재는 UI 테스트 버전입니다)")


# ==========================================
# 탭 2: 내신 변형문제 출제 화면 (PPT 4~5페이지 참고)
# ==========================================
with tab_exam:
    st.subheader("🎯 내신 변형문제 출제 마법사")
    st.info("이전에 만들었던 '지문 선택 -> 문제 유형 선택 -> 2단 PDF 다운로드' 기능이 이 공간에 결합될 예정입니다.")
    
    # 필터만 간단히 우선 구현
    exam_col1, exam_col2, exam_col3 = st.columns(3)
    with exam_col1:
        st.selectbox("대상 학년", ["고1", "고2", "고3"], key="exam_grade", index=1)
    with exam_col2:
        st.selectbox("모의고사 연도", ["2026년", "2025년", "2024년"], key="exam_year")
    
    st.write("<br><br><br><br>*(PPT 4~5페이지의 상세 체크박스와 AI PDF 생성 로직은 다음 단계에서 여기에 이식됩니다.)*", unsafe_allow_html=True)
    
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 12px;'>SDH Premium Decoding & Internal Exam System</div>", unsafe_allow_html=True)
