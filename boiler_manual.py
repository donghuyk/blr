import streamlit as st
import sqlite3
import base64

# 데이터베이스 경로 설정
DB_PATH = "/tmp/pdf_files.db"

# 데이터베이스 초기화
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

# PDF 저장
def save_pdf_to_db(file_name, file_data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO pdf_files (file_name, file_data) VALUES (?, ?)", (file_name, file_data))
    conn.commit()
    conn.close()

# PDF 목록 불러오기
def load_pdf_list_from_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, file_name FROM pdf_files")
    pdf_files = c.fetchall()
    conn.close()
    return pdf_files

# PDF 삭제
def delete_pdf_from_db(file_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM pdf_files WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

# PDF 데이터 불러오기
def load_pdf_data_from_db(file_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT file_data FROM pdf_files WHERE id = ?", (file_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None

# PDF 보기
def show_pdf(file_data):
    base64_pdf = base64.b64encode(file_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# PDF 앱
def app():
    st.title("보일러 메뉴얼 관리")

    # 데이터베이스 초기화
    init_db()

    # 상태 초기화
    if "updated" not in st.session_state:
        st.session_state.updated = False

    # 관리자 모드
    is_admin = st.sidebar.checkbox("관리자 모드 활성화")

    # PDF 업로드
    if is_admin:
        st.sidebar.header("PDF 파일 업로드")
        uploaded_file = st.sidebar.file_uploader("PDF 파일을 업로드하세요", type="pdf")
        if uploaded_file:
            file_name = uploaded_file.name
            file_data = uploaded_file.read()
            save_pdf_to_db(file_name, file_data)
            st.sidebar.success(f"'{file_name}' 파일이 업로드되었습니다!")
            st.session_state.updated = True

    # PDF 삭제
    st.sidebar.header("PDF 파일 삭제")
    pdf_files = load_pdf_list_from_db()
    if pdf_files:
        file_to_delete = st.sidebar.selectbox(
            "삭제할 파일을 선택하세요",
            pdf_files,
            format_func=lambda x: x[1]
        )
        if file_to_delete:
            if st.sidebar.button("삭제"):
                delete_pdf_from_db(file_to_delete[0])
                st.sidebar.success(f"'{file_to_delete[1]}' 파일이 삭제되었습니다!")
                st.session_state.updated = True
    else:
        st.sidebar.write("삭제할 PDF 파일이 없습니다.")

    # 상태 변경에 따른 새로고침
    if st.session_state.updated:
        # 상태를 초기화하여 새로고침 효과를 유도
        st.session_state.updated = False
        st.experimental_rerun()  # Streamlit 페이지 새로고침

    # PDF 목록
    st.sidebar.header("PDF 파일 목록")
    if pdf_files:
        selected_file = st.sidebar.selectbox(
            "PDF 파일을 선택하세요",
            pdf_files,
            format_func=lambda x: x[1]
        )
        if selected_file:
            pdf_data = load_pdf_data_from_db(selected_file[0])
            if pdf_data:
                st.subheader(f"'{selected_file[1]}' 보기")
                show_pdf(pdf_data)
            else:
                st.error("PDF 데이터를 불러오는 데 실패했습니다. 파일이 손상되었거나 삭제되었을 수 있습니다.")
    else:
        st.write("저장된 PDF 파일이 없습니다.")

if __name__ == "__main__":
    app()
