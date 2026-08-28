import streamlit as st
import sqlite3
import pandas as pd
import json
import os

# ==========================================
# 1. 페이지 기본 설정 및 SDH 브랜딩
# ==========================================
st.set_page_config(page_title="SDH Premium V2 - AI 문제은행", layout="wide")

st.markdown("""
<style>
    .group-header { font-weight: 700; font-size: 1.1rem; color: #2C3E50; border-bottom: 2px solid #3498DB; padding-bottom: 8px; margin-top: 20px; margin-bottom: 15px; }
    .status-box { background-color: #E8F8F5; border-left: 5px solid #1ABC9C; padding: 15px; margin: 10px 0; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 무한 캐싱의 핵심: SQLite DB 초기화
# ==========================================
DB_NAME = "sdh_premium_v2.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # [테이블 1] 지문 원문 보관소 (Passages)
    c.execute('''CREATE TABLE IF NOT EXISTS passages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  exam_key TEXT, 
                  q_num TEXT, 
                  passage_text TEXT,
                  UNIQUE(exam_key, q_num))''')
                  
    # [테이블 2] 0원 무한 캐싱 문제은행 (Questions_Cache)
    # 강사가 한 번 출제한 문제나, 원장님이 심야에 일괄 출제한 문제가 이곳에 영구 저장됩니다.
    c.execute('''CREATE TABLE IF NOT EXISTS questions_cache
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  exam_key TEXT, 
                  q_num TEXT, 
                  q_type TEXT, 
                  q_format TEXT, 
                  difficulty TEXT,
                  question TEXT, 
                  passage TEXT, 
                  condition TEXT, 
                  post_text TEXT,
                  options TEXT, 
                  answer TEXT, 
                  explanation TEXT,
                  UNIQUE(exam_key, q_num, q_type, q_format, difficulty))''')
                  
    # [테이블 3] 세종시 기출 패턴 (School_Patterns)
    c.execute('''CREATE TABLE IF NOT EXISTS school_patterns
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  q_type TEXT, 
                  difficulty TEXT, 
                  pattern_text TEXT)''')
                  
    conn.commit()
    conn.close()

# 앱 실행 시 DB가 없으면 자동 생성
init_db()

# ==========================================
# 3. DB 제어용 헬퍼 함수
# ==========================================
def get_db_connection():
    return sqlite3.connect(DB_NAME)

def get_table_count(table_name):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = c.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        return 0

# ==========================================
# 4. 메인 UI (V2 아키텍처 관리자 화면)
# ==========================================
st.markdown("<h2 style='text-align: center;'>SDH Premium Decoding V2 (데이터베이스 모드) 🛠️</h2>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("""
<div class='status-box'>
    <b>🎉 V2 데이터베이스 엔진 가동 중</b><br>
    기존의 불안정한 JSON 파일 방식을 폐기하고, 안전하고 동시 접속에 강한 SQLite 데이터베이스가 성공적으로 연결되었습니다.
</div>
""", unsafe_allow_html=True)

st.markdown("### 📊 현재 SDH 문제은행 DB 적재 현황")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="🗂️ 보관된 지문 원문 (Passages)", value=f"{get_table_count('passages')} 개")
with col2:
    st.metric(label="🎯 0원 무한 캐시 문제 (Questions)", value=f"{get_table_count('questions_cache')} 개")
with col3:
    st.metric(label="🏫 학습된 기출 패턴 (Patterns)", value=f"{get_table_count('school_patterns')} 개")

st.markdown("---")
st.markdown("### 🛠️ DB 시스템 테스트")

# 테스트용 더미 데이터 삽입 로직
if st.button("🧪 [테스트] 고2 모의고사 18번 더미 데이터 DB에 밀어넣기", type="primary"):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # 지문 더미 데이터
        c.execute("INSERT OR IGNORE INTO passages (exam_key, q_num, passage_text) VALUES (?, ?, ?)",
                  ("고등 모의고사_2026년_6월_고2", "18번", "This is a test passage for SDH Premium Decoding."))
        
        # 문제 더미 데이터
        c.execute("""INSERT OR IGNORE INTO questions_cache 
                     (exam_key, q_num, q_type, q_format, difficulty, question, passage, options, answer, explanation) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  ("고등 모의고사_2026년_6월_고2", "18번", "목적", "객관식 전용", "중 (표준/실전)", 
                   "다음 글의 목적으로 가장 적절한 것은?", "This is a test passage for SDH Premium Decoding.", 
                   json.dumps(["① 테스트1", "② 테스트2", "③ 테스트3", "④ 테스트4", "⑤ 테스트5"]), "1", "해설 테스트입니다."))
        conn.commit()
        st.success("✅ 테스트 데이터가 SQLite DB에 완벽하게 저장되었습니다! 화면을 새로고침 해보세요.")
    except Exception as e:
        st.error(f"DB 저장 오류: {e}")
    finally:
        conn.close()

st.markdown("<div style='text-align: center; color: gray; font-size: 12px; margin-top: 50px;'>SDH Premium V2 Architecture - Powered by SQLite & Gemini Flash</div>", unsafe_allow_html=True)
