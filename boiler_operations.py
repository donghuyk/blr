import streamlit as st
import pandas as pd
import sqlite3
import os
import fitz  # PyMuPDF for PDF handling
import base64
import io
from datetime import datetime

# 데이터베이스 파일 경로 설정
DB_DIR = "blr_app"
DB_PATH = os.path.join(DB_DIR, "boiler_operations.db")

# blr_app 폴더가 없으면 생성
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# 데이터베이스 연결 함수
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

# 테이블 생성 함수
def create_tables():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inspection_items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  file_name TEXT,
                  file_data BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS inspection_notes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  file_name TEXT,
                  file_data BLOB)''')
    conn.commit()
    conn.close()

# 점검사항 페이지: PDF 파일 업로드 및 보기
def inspection_items_page(is_admin):
    st.title("점검사항")
    create_tables()

    # 저장된 PDF 보기
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT id, file_name FROM inspection_items")
        rows = c.fetchall()
    except sqlite3.OperationalError:
        # 테이블이 올바르지 않은 경우 테이블을 재생성
        c.execute("DROP TABLE IF EXISTS inspection_items")
        c.execute('''CREATE TABLE inspection_items
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      file_name TEXT,
                      file_data BLOB)''')
        conn.commit()
        rows = []
    conn.close()

    if rows:
        for row in rows:
           
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT file_data FROM inspection_items WHERE id = ?", (row[0],))
            file_data = c.fetchone()[0]
            conn.close()

            if isinstance(file_data, bytes):
                base64_pdf = base64.b64encode(file_data).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
                st.download_button(label="PDF 다운로드", data=file_data, file_name=row[1])

    else:
        st.write("저장된 PDF 파일이 없습니다.")

    # 관리자 모드일 때만 업로드 허용
    if is_admin:
        st.subheader("PDF 파일 업로드")
        uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])
        if uploaded_file is not None:
            file_name = uploaded_file.name
            file_data = uploaded_file.read()

            conn = get_connection()
            c = conn.cursor()
            c.execute('''INSERT INTO inspection_items (file_name, file_data)
                         VALUES (?, ?)''', (file_name, file_data))
            conn.commit()
            conn.close()

            st.success(f"'{file_name}' 파일이 성공적으로 저장되었습니다!")

        # 관리자 모드에서 파일 삭제 기능
        st.sidebar.title("저장된 파일 목록 및 삭제")
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, file_name FROM inspection_items")
        items = c.fetchall()
        conn.close()

        if items:
            file_to_delete = st.sidebar.selectbox("삭제할 파일을 선택하세요", items, format_func=lambda x: x[1])
            if st.sidebar.button("파일 삭제"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("DELETE FROM inspection_items WHERE id = ?", (file_to_delete[0],))
                conn.commit()
                conn.close()
                st.sidebar.success(f"'{file_to_delete[1]}' 파일이 삭제되었습니다.")

# 점검항목 페이지: 엑셀 파일 업로드 및 데이터 표시
def inspection_notes_page(is_admin):
    st.title("점검항목")
    create_tables()

    # 저장된 엑셀 파일 보기
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT id, file_name FROM inspection_notes")
        rows = c.fetchall()
    except sqlite3.OperationalError:
        # 테이블이 올바르지 않은 경우 테이블을 재생성
        c.execute("DROP TABLE IF EXISTS inspection_notes")
        c.execute('''CREATE TABLE inspection_notes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      file_name TEXT,
                      file_data BLOB)''')
        conn.commit()
        rows = []
    conn.close()

    if rows:
        for row in rows:
            
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT file_data FROM inspection_notes WHERE id = ?", (row[0],))
            file_data = c.fetchone()[0]
            conn.close()

            if isinstance(file_data, bytes):
                try:
                    # 엑셀 데이터 읽어서 표시
                    df = pd.read_excel(io.BytesIO(file_data))

                    # 날짜 입력 가능한 열 추가
                    if 'date' not in df.columns:
                        df['date'] = ''

                    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

                    # 저장 버튼 추가
                    if st.button("변경 사항 저장"):
                        # 데이터베이스 업데이트
                        output = io.BytesIO()
                        edited_df.to_excel(output, index=False, engine='openpyxl')
                        updated_data = output.getvalue()

                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE inspection_notes SET file_data = ? WHERE id = ?", (updated_data, row[0]))
                        conn.commit()
                        conn.close()

                        st.success("변경 사항이 저장되었습니다!")

                    st.download_button(label="엑셀 다운로드", data=file_data, file_name=row[1])
                except Exception as e:
                    st.error(f"엑셀 파일 처리 중 오류가 발생했습니다: {e}")
    else:
        st.write("저장된 엑셀 파일이 없습니다.")

    # 관리자 모드일 때만 업로드 허용
    if is_admin:
        st.subheader("엑셀 파일 업로드")
        uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx"])
        if uploaded_file is not None:
            file_name = uploaded_file.name
            file_data = uploaded_file.read()

            conn = get_connection()
            c = conn.cursor()
            c.execute('''INSERT INTO inspection_notes (file_name, file_data)
                         VALUES (?, ?)''', (file_name, file_data))
            conn.commit()
            conn.close()

            st.success(f"'{file_name}' 파일이 성공적으로 저장되었습니다!")

        # 관리자 모드에서 파일 삭제 기능
        st.sidebar.title("저장된 파일 목록 및 삭제")
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, file_name FROM inspection_notes")
        notes = c.fetchall()
        conn.close()

        if notes:
            file_to_delete = st.sidebar.selectbox("삭제할 파일을 선택하세요", notes, format_func=lambda x: x[1])
            if st.sidebar.button("파일 삭제"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("DELETE FROM inspection_notes WHERE id = ?", (file_to_delete[0],))
                conn.commit()
                conn.close()
                st.sidebar.success(f"'{file_to_delete[1]}' 파일이 삭제되었습니다.")

# 사용자 모드와 관리자 모드를 선택하는 함수
def mode_selection():
    st.sidebar.title("모드 선택")
    is_admin = st.sidebar.checkbox("관리자 모드 활성화")
    return is_admin

# 보일러 작업 페이지 함수
def app():
    is_admin = mode_selection()

    st.sidebar.title("보일러 작업")
    page = st.sidebar.selectbox("페이지 선택", ("점검사항", "점검항목"))

    if page == "점검사항":
        inspection_items_page(is_admin)
    elif page == "점검항목":
        inspection_notes_page(is_admin)

# Streamlit 앱 실행
if __name__ == "__main__":
    app()
