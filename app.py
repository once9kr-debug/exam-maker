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

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "is_admin" not in st.session_state: st.session_state.is_admin = False
if "current_page" not in st.session_state: st.session_state.current_page = "list"

# 필터 버튼용 세션 상태
if "f_grade" not in st.session_state: st.session_state.f_grade = "고2"
if "f_year" not in st.session_state: st.session_state.f_year = "2026"
if "f_month" not in st.session_state: st.session_state.f_month = "6월"

# ==========================================
# CSS 스타일링
# ==========================================
st.markdown("""
<style>
    .sdh-logo { font-size: 24px; font-weight: 900; color: #2C3E50; margin-bottom: 20px; text-align: center; border: 1px solid #2C3E50; padding: 20px 0;}
    .disabled-menu { background-color: #D5D8DC; color: #5D6D7E; padding: 15px; text-align: center; border: 1px solid #ABB2B9; margin-bottom: 5px; }
    .active-menu { background-color: #F8F9F9; color: #2C3E50; padding: 15px; text-align: center; border: 1px solid #2C3E50; font-weight: bold; margin-bottom: 5px; }
    
    .filter-box { border: 1px solid #5D6D7E; border-radius: 10px; padding: 20px; margin-bottom: 30px; }
    .filter-label { font-size: 16px; font-weight: bold; text-align: center; padding: 5px; border: 1px solid #5D6D7E; }
    
    .tbl-header { background-color: #4A90E2; color: white; text-align: center; padding: 8px; font-weight: bold; font-size: 16px; border: 1px solid #fff;}
    .tbl-cell { text-align: center; padding: 12px 5px; font-size: 15px; background-color: #EBF5FB; border-bottom: 1px solid #fff;}
    .tbl-cell-alt { text-align: center; padding: 12px 5px; font-size: 15px; background-color: #D6EAF8; border-bottom: 1px solid #fff;}
    
    .exam4you-viewer { column-count: 2; column-gap: 40px; column-rule: 1px solid #ddd; background-color: white; padding: 40px; border: 1px solid #ccc; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); font-family: 'Nanum Myeongjo', serif; }
    .question-box { break-inside: avoid; margin-bottom: 30px; }
    .q-title { font-weight: bold; color: #009688; margin-bottom: 10px; }
    .q-passage { border: 1px solid #000; padding: 10px; margin-bottom: 10px; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 로그인 화면
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<div style='max-width: 400px; margin: 100px auto;'>", unsafe_allow_html=True)
    st.markdown("<div class='sdh-logo'>SDH STUDIO<br><span style='font-size:14px; font-weight:normal;'>(로그인)</span></div>", unsafe_allow_html=True)
    
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
        st.markdown("<div class='sdh-logo'>SDH STUDIO<br><span style='font-size:14px; font-weight:normal;'>(로고)</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='active-menu'>모의고사</div>", unsafe_allow_html=True)
        st.markdown("<div class='disabled-menu'>외부지문</div>", unsafe_allow_html=True)
        st.markdown("<div class='disabled-menu'>교과서</div>", unsafe_allow_html=True)
        
        if st.session_state.is_admin:
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            st.markdown("<div class='disabled-menu'>관리자 모드</div>", unsafe_allow_html=True)
                
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.session_state.is_admin = False
            st.rerun()

    # --- 화면 1: 모의고사 리스트 (새로운 UI 적용) ---
    if st.session_state.current_page == "list":
        
        # 상단 필터 박스
        st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
        
        # 학년 행
        col_g1, col_g2 = st.columns([1, 8])
        with col_g1: st.markdown("<div class='filter-label'>학년</div>", unsafe_allow_html=True)
        with col_g2:
            g_btns = st.columns(10)
            grades = ["고1", "고2", "고3"]
            for i, g in enumerate(grades):
                if g_btns[i].button(g, type="primary" if st.session_state.f_grade == g else "secondary", key=f"g_{g}"):
                    st.session_state.f_grade = g
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 연도 행
        col_y1, col_y2 = st.columns([1, 8])
        with col_y1: st.markdown("<div class='filter-label'>연도</div>", unsafe_allow_html=True)
        with col_y2:
            y_btns = st.columns(12)
            years = ["2026", "2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015"]
            for i, y in enumerate(years):
                if y_btns[i].button(y, type="primary" if st.session_state.f_year == y else "secondary", key=f"y_{y}"):
                    st.session_state.f_year = y
                    st.rerun()
                    
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 월 행
        col_m1, col_m2 = st.columns([1, 8])
        with col_m1: st.markdown("<div class='filter-label'>월</div>", unsafe_allow_html=True)
        with col_m2:
            m_btns = st.columns(10)
            months = ["3월", "4월", "5월", "6월", "7월", "9월", "10월", "11월", "12월"]
            for i, m in enumerate(months):
                if m_btns[i].button(m, type="primary" if st.session_state.f_month == m else "secondary", key=f"m_{m}"):
                    st.session_state.f_month = m
                    st.rerun()
                    
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 출제 버튼 (상단 필터 하단)
        if st.button("출제", type="primary", use_container_width=True):
            st.session_state.current_page = "select"
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 하단 DB 리스트 표 (Custom Table)
        # 테이블 헤더
        h1, h2, h3, h4, h5, h6 = st.columns([1, 1, 1, 1, 2, 1.5])
        h1.markdown("<div class='tbl-header'>No.</div>", unsafe_allow_html=True)
        h2.markdown("<div class='tbl-header'>학년</div>", unsafe_allow_html=True)
        h3.markdown("<div class='tbl-header'>연도</div>", unsafe_allow_html=True)
        h4.markdown("<div class='tbl-header'>월</div>", unsafe_allow_html=True)
        h5.markdown("<div class='tbl-header'>업로드일</div>", unsafe_allow_html=True)
        h6.markdown("<div class='tbl-header'>출제</div>", unsafe_allow_html=True)
        
        # DB 더미 데이터
        db_history = [
            {"no": 5, "grade": "2", "year": "2026", "month": "3", "date": "2026-08-29"},
            {"no": 4, "grade": "3", "year": "2015", "month": "4", "date": "2026-08-29"},
            {"no": 3, "grade": "2", "year": "2022", "month": "6", "date": "2026-08-29"},
            {"no": 2, "grade": "3", "year": "2025", "month": "11", "date": "2026-08-29"},
            {"no": 1, "grade": "1", "year": "2026", "month": "9", "date": "2026-08-29"},
        ]
        
        # 테이블 본문 생성
        for idx, row in enumerate(db_history):
            cell_class = "tbl-cell-alt" if idx % 2 == 0 else "tbl-cell"
            
            c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 2, 1.5])
            c1.markdown(f"<div class='{cell_class}'>{row['no']}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='{cell_class}'>{row['grade']}</div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='{cell_class}'>{row['year']}</div>", unsafe_allow_html=True)
            c4.markdown(f"<div class='{cell_class}'>{row['month']}</div>", unsafe_allow_html=True)
            c5.markdown(f"<div class='{cell_class}'>{row['date']}</div>", unsafe_allow_html=True)
            with c6:
                st.markdown(f"<div style='background-color: {'#D6EAF8' if idx%2==0 else '#EBF5FB'}; padding:5px;'>", unsafe_allow_html=True)
                if st.button("출제", key=f"btn_out_{row['no']}", use_container_width=True):
                    # 출제 버튼 클릭 시 선택한 값을 세션에 저장하고 페이지 이동 가능
                    st.session_state.current_page = "select"
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # --- 화면 2: 문제 출제 (조건 선택) ---
    elif st.session_state.current_page == "select":
        st.subheader(f"모의고사 {st.session_state.f_year}년-{st.session_state.f_month}, {st.session_state.f_grade}")
        
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
        st.subheader(f"[ {st.session_state.f_year}년도 {st.session_state.f_month} {st.session_state.f_grade} 모의고사 ]")
        
        c_v1, c_v2, c_v3 = st.columns(3)
        with c_v1:
            st.radio("문제지 형식", ["1단", "2단"], index=1, horizontal=True)
        with c_v2:
            st.radio("문제 난이도", ["상,중,하 혼합", "상", "중", "하"], horizontal=True)
            
        st.markdown("<hr>", unsafe_allow_html=True)
        
        d1, d2, d3 = st.columns(3)
        with d1: st.button("📥 문제지 다운로드 (HWP/Docx)", type="primary", use_container_width=True)
        with d2: st.button("📥 정답지 다운로드", use_container_width=True)
        with d3: st.button("⬅️ 출제 화면으로 돌아가기", use_container_width=True, on_click=lambda: st.session_state.update(current_page="select"))
            
        st.markdown("<br>", unsafe_allow_html=True)
        
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
