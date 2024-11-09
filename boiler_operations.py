import streamlit as st
import pandas as pd
import sqlite3
import os
import fitz  # PyMuPDF for PDF handling
import base64

# 데이터베이스 파일 경로 설정
DB_DIR = "blr_app"
DB_PATH = os.path.join(DB_DIR, "boiler_operations.db")

# blr_app 폴더가 없으면 생성
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# 데이터베이스 연결 함수 (check_same_thread=False로 설정)
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

# 테이블 생성 함수 (점검항목, 점검사항)
def create_tables():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inspection_items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  table_name TEXT,
                  data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS inspection_notes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  file_name TEXT,
                  file_data BLOB)''')
    conn.commit()
    conn.close()

# 점검항목 PDF 파일에서 표 추출 및 데이터 저장 함수
def extract_and_save_inspection_items(pdf_file):
    try:
        file_data = pdf_file.read()
        with fitz.open(stream=file_data, filetype="pdf") as pdf:
            conn = get_connection()
            c = conn.cursor()
            for page_number in range(len(pdf)):
                page = pdf.load_page(page_number)
                tables = page.get_text("blocks")
                for table in tables:
                    table_name = f"Page {page_number + 1} Table"
                    c.execute('''INSERT INTO inspection_items (table_name, data)
                                 VALUES (?, ?)''', (table_name, str(table)))
            conn.commit()
            conn.close()
    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

# 점검사항 PDF 파일에서 파일 데이터 저장 함수
def extract_and_save_inspection_notes(pdf_file):
    try:
        file_name = pdf_file.name
        file_data = pdf_file.read()
        
        create_tables()  # 테이블 생성 보장
        
        conn = get_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO inspection_notes (file_name, file_data)
                     VALUES (?, ?)''', (file_name, file_data))
        conn.commit()
        conn.close()
        
        st.success(f"'{file_name}' 파일이 성공적으로 저장되었습니다!")

    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

# 점검항목 페이지 함수 (사용자/관리자 모드)
def inspection_items_page(is_admin):
    st.title("점검항목")
    create_tables()

    # 저장된 데이터 표시
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM inspection_items")
    rows = c.fetchall()
    if rows:
        data = [eval(row[2]) for row in rows]
        df = pd.DataFrame(data)
        st.write(df)
    else:
        st.write("저장된 데이터가 없습니다.")
    conn.close()

    # 관리자 모드일 때만 업로드 허용
    if is_admin:
        st.subheader("점검항목 파일 업로드")
        uploaded_file = st.file_uploader("점검항목 PDF 파일을 업로드하세요", type=["pdf"])
        if uploaded_file is not None:
            extract_and_save_inspection_items(uploaded_file)
            st.success("점검항목 PDF 파일에서 데이터를 추출하고 데이터베이스에 저장했습니다.")

    # 관리자 모드일 때만 파일 삭제 허용
    if is_admin:
        st.sidebar.title("저장된 파일 목록 및 삭제")
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, table_name FROM inspection_items")
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

# 점검사항 페이지 함수 (사용자/관리자 모드)
def inspection_notes_page(is_admin):
    st.title("점검사항")
    create_tables()

    # 저장된 데이터 표시
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT id, file_name FROM inspection_notes")
        rows = c.fetchall()
    except sqlite3.OperationalError:
        # 테이블에 file_name 열이 없는 경우 테이블을 재생성
        c.execute("DROP TABLE IF EXISTS inspection_notes")
        c.execute('''CREATE TABLE inspection_notes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      file_name TEXT,
                      file_data BLOB)''')
        conn.commit()
        c.execute("SELECT id, file_name FROM inspection_notes")
        rows = c.fetchall()
    conn.close()

    if rows:
        for row in rows:
            st.subheader(f"파일 이름: {row[1]}")
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT file_data FROM inspection_notes WHERE id = ?", (row[0],))
            file_data = c.fetchone()[0]
            conn.close()
            if isinstance(file_data, bytes):
                try:
                    base64_pdf = base64.b64encode(file_data).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                    st.download_button(label="PDF 파일 다운로드", data=file_data, file_name=row[1])
                except Exception as e:
                    st.error(f"PDF 표시 중 오류가 발생했습니다: {e}")
            else:
                st.error("파일 데이터 형식이 올바르지 않습니다.")
    else:
        st.write("저장된 데이터가 없습니다.")

    # 관리자 모드일 때만 업로드 허용
    if is_admin:
        st.subheader("점검사항 파일 업로드")
        uploaded_file = st.file_uploader("점검사항 PDF 파일을 업로드하세요", type=["pdf"])
        if uploaded_file is not None:
            extract_and_save_inspection_notes(uploaded_file)

    # 관리자 모드일 때만 파일 삭제 허용
    if is_admin:
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
    page = st.sidebar.selectbox("페이지 선택", ("점검항목", "점검사항"))

    if page == "점검항목":
        inspection_items_page(is_admin)
    elif page == "점검사항":
        inspection_notes_page(is_admin)

# Streamlit 앱 실행
if __name__ == "__main__":
    app()