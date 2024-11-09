import streamlit as st
import datetime
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from streamlit_pdf_viewer import pdf_viewer
from PIL import Image
import sqlite3
from datetime import date
from io import BytesIO
import fitz
import io
import base64
import matplotlib.dates as mdates

def app():
    st.title("보일러 메뉴얼")
    
    
    # 데이터베이스 초기화 함수
    def init_db():
        conn = sqlite3.connect('pdf_files.db')
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
        conn = sqlite3.connect('pdf_files.db')
        c = conn.cursor()
        c.execute('INSERT INTO pdf_files (file_name, file_data) VALUES (?, ?)', (file_name, file_data))
        conn.commit()
        conn.close()

    # 데이터베이스에서 저장된 PDF 파일 목록을 불러오는 함수
    def load_pdf_list_from_db():
        conn = sqlite3.connect('pdf_files.db')
        c = conn.cursor()
        c.execute('SELECT id, file_name FROM pdf_files')
        pdf_files = c.fetchall()
        conn.close()
        return pdf_files

    # 특정 PDF 파일을 데이터베이스에서 불러오는 함수
    def load_pdf_data_from_db(file_id):
        conn = sqlite3.connect('pdf_files.db')
        c = conn.cursor()
        c.execute('SELECT file_data FROM pdf_files WHERE id = ?', (file_id,))
        pdf_data = c.fetchone()[0]
        conn.close()
        return pdf_data

    # PDF 데이터를 base64로 인코딩하여 iframe에 표시하는 함수
    def show_pdf(file_data):
        base64_pdf = base64.b64encode(file_data).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

    # 데이터베이스 초기화
    init_db()

    # Streamlit UI 구성

    # PDF 파일 업로드 기능 (관리자 모드에서만 가능)
    is_admin = st.sidebar.checkbox("관리자 모드 활성화")
    if is_admin:
        uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")

        if uploaded_file is not None:
            file_name = uploaded_file.name
            file_data = uploaded_file.read()

            # PDF 파일을 데이터베이스에 저장
            save_pdf_to_db(file_name, file_data)
            st.success(f"'{file_name}' 파일이 성공적으로 저장되었습니다!")

    # 데이터베이스에서 저장된 PDF 파일 목록 불러오기
    pdf_files = load_pdf_list_from_db()

    # 저장된 PDF 파일 목록을 사이드바에 표시 (관리자 모드에서만 가능)
    if is_admin and pdf_files:
        st.sidebar.title("저장된 PDF 파일 목록")
        file_selection = st.sidebar.selectbox("PDF 파일을 선택하세요", pdf_files, format_func=lambda x: x[1])
        
        if file_selection:
            selected_file_id = file_selection[0]
            selected_file_name = file_selection[1]
            
            # 선택한 PDF 파일의 데이터를 불러오기
            pdf_data = load_pdf_data_from_db(selected_file_id)
            
            # PDF 파일을 Streamlit에서 보여줌
            show_pdf(pdf_data)
            st.download_button(label="PDF 파일 다운로드", data=pdf_data, file_name=selected_file_name)
    elif not is_admin and pdf_files:
       
        file_selection = st.selectbox("PDF 파일을 선택하세요", pdf_files, format_func=lambda x: x[1])
        
        if file_selection:
            selected_file_id = file_selection[0]
            selected_file_name = file_selection[1]
            
            # 선택한 PDF 파일의 데이터를 불러오기
            pdf_data = load_pdf_data_from_db(selected_file_id)
            
            # PDF 파일을 Streamlit에서 보여줌
            show_pdf(pdf_data)
            st.download_button(label="PDF 파일 다운로드", data=pdf_data, file_name=selected_file_name)
    else:
        st.sidebar.write("저장된 PDF 파일이 없습니다.")
