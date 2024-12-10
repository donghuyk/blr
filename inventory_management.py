import streamlit as st
import sqlite3
import os
import pandas as pd
import io

# 데이터베이스 파일 경로 설정
DB_DIR = "blr_app"
DB_PATH = os.path.join(DB_DIR, "inventory.db")

# blr_app 폴더가 없으면 생성
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# 데이터베이스 연결 함수
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

# 테이블 생성 함수
def create_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            file_data BLOB
        )
    ''')
    conn.commit()
    conn.close()

# 데이터베이스 초기화 함수 (기존 데이터 삭제)
def reset_database():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS inventory")
    conn.commit()
    conn.close()
    create_table()

# 데이터베이스에 데이터 삽입
def insert_data(file_name, file_data):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO inventory (file_name, file_data)
        VALUES (?, ?)
    ''', (file_name, file_data))
    conn.commit()
    conn.close()

# 데이터베이스에서 데이터 조회
def view_data():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, file_name FROM inventory")
    data = c.fetchall()
    conn.close()
    return data

# 데이터베이스에서 파일 데이터 삭제
def delete_file(file_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM inventory WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

# 재고관리 페이지 함수
def app():
    st.title("재고관리")

    # 관리자 모드 체크박스
    is_admin = st.sidebar.checkbox("관리자 모드 활성화")

    # 데이터베이스 초기화 옵션 (관리자 전용)
    if is_admin and st.sidebar.button("데이터베이스 초기화"):
        reset_database()
        st.sidebar.success("데이터베이스가 초기화되었습니다.")

    # 테이블 생성
    create_table()

    # 파일 업로드 UI (관리자 모드에서만 가능)
    if is_admin:
        uploaded_file = st.file_uploader("Excel 파일을 업로드하세요", type=["xlsx"])

        # 파일 업로드된 경우 처리
        if uploaded_file is not None:
            file_name = uploaded_file.name
            file_data = uploaded_file.read()

            # 데이터베이스에 저장
            insert_data(file_name, file_data)
            st.success(f"'{file_name}' 파일이 성공적으로 저장되었습니다.")

    # 데이터베이스에서 데이터를 조회하고 표시
    
    stored_files = view_data()

    if stored_files:
        for file_id, file_name in stored_files:
            

            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT file_data FROM inventory WHERE id = ?", (file_id,))
            file_data = c.fetchone()[0]
            conn.close()

            if isinstance(file_data, bytes):
                try:
                    df = pd.read_excel(io.BytesIO(file_data))
                  
                    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

                    if st.button(f"변경 사항 저장"):
                        output = io.BytesIO()
                        edited_df.to_excel(output, index=False, engine='openpyxl')
                        updated_data = output.getvalue()

                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE inventory SET file_data = ? WHERE id = ?", (updated_data, file_id))
                        conn.commit()
                        conn.close()

                        st.success("변경 사항이 저장되었습니다!")

                    st.download_button(label="엑셀 다운로드", data=file_data, file_name=file_name)
                except Exception as e:
                    st.error(f"엑셀 파일 처리 중 오류가 발생했습니다: {e}")

        # 관리자 모드에서 파일 삭제 기능 추가
        if is_admin:
            st.subheader("파일 삭제")
            file_to_delete = st.selectbox("삭제할 파일을 선택하세요", stored_files, format_func=lambda x: x[1])
            if st.button("선택된 파일 삭제"):
                delete_file(file_to_delete[0])
                st.success(f"'{file_to_delete[1]}' 파일이 삭제되었습니다. 페이지를 다시 로드하세요.")
    else:
        st.write("저장된 파일이 없습니다.")

# Streamlit 앱 실행
if __name__ == "__main__":
    app()
