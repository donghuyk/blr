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
import qrcode

import boiler_manual
import inventory_management
import troubleshooting
import boiler_operations

# 사이드바에서 페이지 선택
page = st.sidebar.selectbox(
    "페이지 선택",
    ("보일러 메뉴얼", "재고관리", "Trouble Shooting", "보일러 작업", "QR 코드 생성")
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
elif page == "QR 코드 생성":
    st.title("QR 코드 생성 및 공유")

    # 웹 애플리케이션 URL 설정 (여기에 실제 웹 URL을 사용하세요)
    web_url = "http://localhost:8501"  # 배포된 웹 URL로 변경 필요

    # QR 코드 생성
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(web_url)
    qr.make(fit=True)

    # QR 코드 이미지를 생성
    img = qr.make_image(fill_color="black", back_color="white")

    # Streamlit으로 QR 코드 이미지 표시
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    st.image(buffer.getvalue(), caption="이 QR 코드를 스캔하여 웹 애플리케이션에 접속하세요.")

    # QR 코드 이미지 다운로드 버튼 추가
    buffer.seek(0)
    st.download_button(label="QR 코드 다운로드", data=buffer, file_name="web_qr_code.png", mime="image/png")
