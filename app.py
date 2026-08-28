import streamlit as st
import sqlite3
import pandas as pd
import json
import docx
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from io import BytesIO

# ==========================================
# 1. 페이지 설정 및 세션 상태 초기화
# ==========================================
st.set_page_config(page_title="SDH STUDIO", layout="wide", initial_sidebar_state="expanded")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "list" # list, select, viewer

# ==========================================
# CSS 스타일링
# ==========================================
st.markdown("""
<style>
    .sdh-logo { font-size: 24px; font-weight: 900; color: #2C3E50; margin-bottom: 20px; text-align: center; }
    .disabled-menu { color: #A6ACAF; cursor: not-allowed; padding: 10px 0; }
    .active-menu { color: #2980B9; font-weight: bold; padding: 10px 0; border-right: 3px solid #2980B9; }
    .exam4you-viewer { column-count: 2; column-gap: 40px; column-rule: 1px solid #ddd; background-color: white; padding: 40px; border: 1px solid #ccc; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); font-family: 'Nanum Myeongjo', serif; }
    .question-box { break-inside: avoid; margin-bottom: 30px; }
    .q-title { font-weight: bold; color: #009688; margin-bottom: 10px; }
    .q-passage { border: 1px solid #000; padding: 10px; margin-bottom: 10px; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 기본 HWP/Docx 렌더링 엔진 (임시 쌩얼 버전)
# ==========================================
def generate_base_document():
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.6)
        section.right_margin = Inches(0.6)
        sectPr = section._sectPr
        cols = OxmlElement('w:cols')
        cols.set(qn('w:num'), '2')
        cols.set(qn('w:space'), '720')
        sectPr.append(cols)

    heading = doc.add_heading('SDH Premium Decoding - 2026년 6월 고2 모의고사', level=1)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("1. 다음 글의 밑줄 친 (A)its \"future-proof\" nature가 의미하는 바로 알맞은 것은?").bold = True
    doc.add_paragraph("One easily underappreciated feature of a city street or square is (A)its 'future-proof' nature...")
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ==========================================
# 2. 로그인 화면
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<div style='max-width: 400px; margin: 100px auto;'>", unsafe_allow_html=True)
    st.markdown("<div class='sdh-logo'>SDH STUDIO</div>", unsafe_allow_html=True)
    
    user_id = st.text_input("ID")
    user_pw = st.text_input("PW", type="password")
    
    if st.button("로그인", use_container_width=True, type="primary"):
        if user_id == "admin" and user_pw == "1234":
            st.session_state.logged_in = True
            st.session_state.is_admin = True
            st.rerun()
        elif user_id == "teacher" and user_pw == "1234":
            st.session_state.logged_in = True
            st.session_state.is_admin = False
            st.rerun()
        else:
            st.error("ID 또는 PW가 일치하지 않습니다.")
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 3. 메인 화면 (로그인 성공 시)
# ==========================================
else:
    # --- 사이드바 메뉴 ---
    with st.sidebar:
        st.markdown("<div class='sdh-logo'>SDH STUDIO</div>", unsafe_allow_html=True)
        st.markdown("<div class='active-menu'>📝 모의고사</div>", unsafe_allow_html=True)
        st.markdown("<div class='disabled-menu'>📄 외부지문 (준비중)</div>", unsafe_allow_html=True)
        st.markdown("<div class='disabled-menu'>📚 교과서 (준비중)</div>", unsafe_allow_html=True)
        
        if st.session_state.is_admin:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("<b>⚙️ 관리자 모드</b>", unsafe_allow_html=True)
            if st.button("심야 일괄 출제(Batch)", use_container_width=True):
                st.info("일괄 출제 기능은 추후 연동됩니다.")
                
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.session_state.is_admin = False
            st.rerun()

    # --- 화면 1: 모의고사 리스트 ---
    if st.session_state.current_page == "list":
        st.subheader("모의고사")
        
        # 필터 영역
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        with col1: st.selectbox("학교/급", ["고등", "중등"])
        with col2: st.selectbox("분류", ["모의고사"])
        with col3: st.selectbox("연도", ["2026", "2025"])
        with col4: st.selectbox("월", ["6월", "3월", "11월"])
        with col5: st.button("검색 🔍")
            
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # 더미 리스트 (데이터프레임 활용)
        df = pd.DataFrame({
            "연도": ["2026", "2026", "2026"],
            "월": ["6", "6", "6"],
            "주관": ["2026년 6월", "2026년 6월", "2026년 6월"],
            "학년": ["1학년", "2학년", "3학년"],
            "문제수": [329, 323, 281]
        })
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        if st.button("👉 고2 2026년 6월 모의고사 출제하기 (보기 버튼 대체)"):
            st.session_state.current_page = "select"
            st.rerun()

    # --- 화면 2: 문제 출제 (조건 선택) ---
    elif st.session_state.current_page == "select":
        st.subheader("모의고사 2026년-6월, 2학년, 고2")
        
        st.write("**1. 출제 유형 선택**")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.checkbox("대의 파악 (주제/요지/제목)", value=True)
        with c2: st.checkbox("언어 논리 (빈칸/순서/삽입)", value=True)
        with c3: st.checkbox("어법/어휘")
        with c4: st.checkbox("서술형")
            
        st.write("**2. 지문(문제) 번호 선택**")
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1: st.checkbox("18번 (목적)")
        with c_p2: st.checkbox("19번 (심경)")
        with c_p3: st.checkbox("20번 (주장)")
            
        st.markdown("<hr>", unsafe_allow_html=True)
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            st.info("현재 선택된 조건으로 총 **45문제**가 준비되어 있습니다.")
            if st.button("📖 선택 문제 보기", type="primary", use_container_width=True):
                st.session_state.current_page = "viewer"
                st.rerun()
        
        if st.button("⬅️ 목록으로 돌아가기"):
            st.session_state.current_page = "list"
            st.rerun()

    # --- 화면 3: 웹 뷰어 및 출력 ---
    elif st.session_state.current_page == "viewer":
        st.subheader("[ 2026년도 6월 2학년 고2 모의고사 ]")
        
        c_v1, c_v2, c_v3 = st.columns(3)
        with c_v1:
            st.radio("문제지 형식", ["1단", "2단"], index=1, horizontal=True)
        with c_v2:
            st.radio("문제 난이도", ["상,중,하 혼합", "상", "중", "하"], horizontal=True)
            
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # 다운로드 버튼 영역
        d1, d2, d3 = st.columns(3)
        exam_file = generate_base_document()
        with d1:
            st.download_button(label="📥 문제지 다운로드 (HWP/Docx)", data=exam_file, file_name="SDH_Exam.docx", type="primary", use_container_width=True)
        with d2:
            st.button("📥 정답지 다운로드", use_container_width=True)
        with d3:
            st.button("⬅️ 출제 화면으로 돌아가기", use_container_width=True, on_click=lambda: st.session_state.update(current_page="select"))
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2단 뷰어 HTML
        viewer_html = """
        <div class='exam4you-viewer'>
            <div class='question-box'>
                <div class='q-title'>1. 다음 글의 밑줄 친 (A)its "future-proof" nature가 의미하는 바로 알맞은 것은? [18]</div>
                <div class='q-passage'>One easily underappreciated feature of a city street or square is (A)<u>its "future-proof" nature</u>. (생략)</div>
                <div style='text-align: right;'><button style='padding:2px 8px;'>✏️수정</button> <button style='padding:2px 8px;'>🔄재출제</button></div>
            </div>
            <div class='question-box'>
                <div class='q-title'>2. 다음 빈칸에 들어갈 말로 가장 적절한 것은? [19]</div>
                <div class='q-passage'>The genomics revolution made it possible to see just how impactful touch is to plants...</div>
                <div style='text-align: right;'><button style='padding:2px 8px;'>✏️수정</button> <button style='padding:2px 8px;'>🔄재출제</button></div>
            </div>
        </div>
        """
        st.markdown(viewer_html, unsafe_allow_html=True)
