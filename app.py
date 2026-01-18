import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

st.title("🛠️ בדיקת חיבור ידנית לגוגל")

try:
    # 1. חילוץ המידע הגולמי מה-Secrets
    sa_info = json.loads(st.secrets.connections.gsheets.service_account)
    spreadsheet_id = st.secrets.connections.gsheets.spreadsheet.split("/d/")[1].split("/")[0]
    
    # 2. ניסיון יצירת Credentials ידני
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=scopes)
    
    # 3. ניסיון קריאה ראשוני
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range="sheet1!A1:B10").execute()
    
    st.success("✅ הצלחתי להתחבר ידנית!")
    st.write("נתונים שנקראו:", result.get('values', []))

except Exception as e:
    st.error("❌ כשל באימות מול גוגל")
    # כאן נראה את הודעת השגיאה המקורית של גוגל
    st.code(str(e))
    
    if "401" in str(e) or "unauthorized" in str(e).lower():
        st.warning("💡 ה-Private Key לא תקין או שה-Secrets לא התעדכנו בשרת.")
        st.info("בצע Reboot לאפליקציה ב-Dashboard.")
