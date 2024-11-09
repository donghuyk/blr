import streamlit as st
import pandas as pd
import sqlite3
import os

# 데이터베이스 파일 경로 설정
DB_DIR = "blr_app"
DB_PATH = os.path.join(DB_DIR, "inventory.db")

# blr_app 폴더가 없으면 생성
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# 데이터베이스 연결 함수 (check_same_thread=False로 설정)
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

# 테이블이 없을 경우 생성
def create_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventory
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  part_name TEXT,
                  part_number TEXT,
                  available_quantity INTEGER,
                  required_quantity INTEGER)''')
    conn.commit()
    conn.close()

# 데이터베이스에 데이터 삽입
def insert_data(df):
    conn = get_connection()
    c = conn.cursor()
    for _, row in df.iterrows():
        c.execute('''
            INSERT INTO inventory (part_name, part_number, available_quantity, required_quantity)
            VALUES (?, ?, ?, ?)
        ''', (row['Part Name'], row['Part Number'], row['Available Quantity'], row['Required Quantity']))
    conn.commit()
    conn.close()

# 데이터베이스에서 데이터 조회
def view_data():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM inventory")
    data = c.fetchall()
    conn.close()
    return data

# 데이터베이스에서 수량 업데이트
def update_quantity(item_id, new_available_quantity, new_required_quantity):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE inventory 
        SET available_quantity = ?, required_quantity = ? 
        WHERE id = ?
    ''', (new_available_quantity, new_required_quantity, item_id))
    conn.commit()
    conn.close()

# Excel 파일을 읽어 데이터프레임으로 변환
def load_excel(file):
    df = pd.read_excel(file, engine='openpyxl')
    return df

# 재고 관리 페이지 함수
def app():
    st.title("재고 관리")

    # 관리자 모드 체크박스
    is_admin = st.sidebar.checkbox("관리자 모드 활성화")

    # 테이블 생성
    create_table()

    # 파일 업로드 UI (관리자 모드에서만 가능)
    if is_admin:
        uploaded_file = st.file_uploader("Excel 파일을 업로드하세요", type=["xlsx"])

        # 파일 업로드된 경우 처리
        if uploaded_file is not None:
            # Excel 파일을 데이터프레임으로 불러오기
            df = load_excel(uploaded_file)
            
            # 데이터베이스에 자동으로 저장
            insert_data(df)
            st.success("업로드된 데이터가 데이터베이스에 자동으로 저장되었습니다.")

    # 데이터베이스에서 데이터를 조회하고 편집 가능한 테이블로 표시
    st.write("저장된 데이터:")
    stored_data = view_data()

    if stored_data:
        # 데이터베이스에서 불러온 데이터를 데이터프레임으로 변환 (컬럼 이름 설정)
        df = pd.DataFrame(stored_data, columns=["ID", "Part Name", "Part Number", "Available Quantity", "Required Quantity"])

        # 데이터 편집 가능하게 표시 (키보드로 수량 수정 가능, 관리자 모드에서만 가능)
        if is_admin:
            edited_df = st.data_editor(df[['ID', 'Part Name', 'Part Number', 'Available Quantity', 'Required Quantity']],
                                       num_rows="dynamic", key='editable_table')

            # 변경 사항 저장 시 데이터베이스에 업데이트
            if st.button("변경 사항 저장"):
                for index, row in edited_df.iterrows():
                    update_quantity(row['ID'], row['Available Quantity'], row['Required Quantity'])
                st.success("모든 변경 사항이 저장되었습니다.")
        else:
            st.write(df)
    else:
        # 데이터가 없을 때의 메시지
        st.write("저장된 데이터가 없습니다. Excel 파일을 업로드해 주세요.")

# Streamlit 앱 실행
if __name__ == "__main__":
    app()
