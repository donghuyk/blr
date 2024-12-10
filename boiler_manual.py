import streamlit as st
import sqlite3
from io import BytesIO
import base64
import os
import tempfile

def app():
    st.title("보일러 메뉴얼 관리")
    
    # 데이터베이스 경로 설정 (Streamlit Cloud 환경에서는 `/tmp` 디렉토리 사용)
    DB_PATH = "/tmp/pdf_files.db"
    
    # 데이터베이스 초기화 함수
    def init_db():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS pdf_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                file_data BLOB
            )
        ''')
        conn.commit()
        conn.close()

    # PDF 파일을 데이터베이스에 저장하는 함수
    def save_pdf_to_db(file_name, file_data):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO pdf_files (file_name, file_data) VALUES (?, ?)', (file_name, file_data))
        conn.commit()
        conn.close()

    # 데이터베이스에서 저장된 PDF 파일 목록 불러오기
    def load_pdf_list_from_db():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, file_name FROM pdf_files')
        pdf_files = c.fetchall()
        conn.close()
        return pdf_files

    # 특정 PDF 파일 데이터를 불러오는 함수
    def load_pdf_data_from_db(file_id):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT file_data FROM pdf_files WHERE id = ?', (file_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    # 특정 PDF 파일을 데이터베이스에서 삭제하는 함수
    def delete_pdf_from_db(file_id):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM pdf_files WHERE id = ?', (file_id,))
        conn.commit()
        conn.close()

    # PDF를 브라우저 새 탭에서 열 수 있는 링크 생성 함수
    def show_pdf_new_tab(file_data, file_name):
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file_data)
            tmp_file_path = tmp_file.name
        
        # 링크를 통해 새 탭에서 PDF 열기
        st.markdown(
            f'[**PDF 새 탭에서 보기**](file://{tmp_file_path})',
            unsafe_allow_html=True
        )
        
        # PDF 다운로드 버튼 제공
        st.download_button(
            label="PDF 다운로드",
            data=file_data,
            file_name=file_name,
            mime="application/pdf"
        )

    # 데이터베이스 초기화
    init_db()

    # 관리자 모드 활성화
    is_admin = st.sidebar.checkbox("관리자 모드 활성화")
    
    # 관리자 모드 기능
    if is_admin:
        st.sidebar.header("PDF 파일 업로드")
        uploaded_file = st.sidebar.file_uploader("PDF 파일을 업로드하세요", type="pdf")
        if uploaded_file is not None:
            file_name = uploaded_file.name
            file_data = uploaded_file.read()
            save_pdf_to_db(file_name, file_data)
            st.sidebar.success(f"'{file_name}' 파일이 성공적으로 저장되었습니다!")
        
        # 저장된 PDF 파일 목록에서 삭제 기능 추가
        st.sidebar.header("PDF 파일 삭제")
        pdf_files = load_pdf_list_from_db()
        if pdf_files:
            file_to_delete = st.sidebar.selectbox(
                "삭제할 파일을 선택하세요",
                pdf_files,
                format_func=lambda x: x[1]  # 파일 이름만 표시
            )
            if st.sidebar.button("삭제"):
                delete_pdf_from_db(file_to_delete[0])
                st.sidebar.success(f"'{file_to_delete[1]}' 파일이 삭제되었습니다!")
                st.experimental_rerun()  # 삭제 후 페이지 새로고침
        else:
            st.sidebar.write("삭제할 PDF 파일이 없습니다.")

    # 저장된 PDF 파일 목록 가져오기
    pdf_files = load_pdf_list_from_db()

    # PDF 파일 목록 표시
    if pdf_files:
        st.sidebar.header("PDF 파일 목록")
        selected_file = st.sidebar.selectbox(
            "PDF 파일을 선택하세요",
            pdf_files,
            format_func=lambda x: x[1]  # 파일 이름만 표시
        )

        if selected_file:
            selected_file_id = selected_file[0]
            selected_file_name = selected_file[1]
            pdf_data = load_pdf_data_from_db(selected_file_id)
            
            if pdf_data:
                # PDF 새 탭에서 보기 및 다운로드 제공
                st.subheader(f"'{selected_file_name}' 보기")
                show_pdf_new_tab(pdf_data, selected_file_name)
    else:
        st.write("저장된 PDF 파일이 없습니다. PDF 파일을 업로드하세요!")

if __name__ == "__main__":
    app()
