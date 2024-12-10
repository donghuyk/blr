import streamlit as st
import datetime
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from PIL import Image
import sqlite3
from datetime import date
from io import BytesIO
import fitz  # PyMuPDF for PDF processing
import base64
import matplotlib.dates as mdates
import qrcode

import boiler_manual
import inventory_management
import troubleshooting
import boiler_operations

# 사이드바에서 페이지 선택
page = st.sidebar.selectbox(
    "페이지 선택",
    ("보일러 메뉴얼", "재고관리", "Trouble Shooting", "보일러 작업", "RAG")
)

# 선택된 페이지에 따라 해당 모듈 실행
if page == "보일러 메뉴얼":
    boiler_manual.app()
elif page == "재고관리":
    inventory_management.app()
elif page == "Trouble Shooting":
    troubleshooting.app()
elif page == "보일러 작업":
    boiler_operations.app()
elif page == "RAG":
    st.title("RAG (Retrieve and Generate)")
    st.markdown("**RAG 페이지에 오신 것을 환영합니다!**")
    st.write("여기에서 RAG 관련 링크 및 기능을 확인할 수 있습니다.")

    # 링크 버튼 추가
    RAG_link = st.button("Go to RAG Documentation")
    GPT_link = st.button("Go to GPT Model")

    if RAG_link:
        st.write("RAG 관련 문서 링크로 이동 중입니다...")
        st.markdown("[Visit RAG Documentation](https://example.com/rag-docs)")

    if GPT_link:
        st.write("GPT 모델 관련 링크로 이동 중입니다...")
        st.markdown("[Visit GPT Model](https://example.com/gpt)")

# PDF 파일 표시 함수
def show_pdf(file_data):
    base64_pdf = base64.b64encode(file_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# PDF 파일을 데이터베이스에서 불러와 보여주는 함수
def load_and_display_pdf_from_db(database_path, file_id):
    conn = sqlite3.connect(database_path)
    c = conn.cursor()
    c.execute('SELECT file_data FROM pdf_files WHERE id = ?', (file_id,))
    pdf_data = c.fetchone()[0]
    conn.close()

    show_pdf(pdf_data)
