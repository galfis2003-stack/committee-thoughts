import streamlit as st
import pandas as pd
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

# --- פונקציות חיבור ---
def get_sheet_service():
    sa_info = json.loads(st.secrets.connections.gsheets.service_account)
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=scopes)
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()

def read_data():
    spreadsheet_id = st.secrets.connections.gsheets.spreadsheet.split("/d/")[1].split("/")[0]
    sheet = get_sheet_service()
    # קריאת כל הטווח כולל כותרות
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range="sheet1!A:B").execute()
    values = result.get('values', [])
    if not values:
        return pd.DataFrame(columns=["meeting", "thought"])
    return pd.DataFrame(values[1:], columns=values[0])

def save_data(df):
    spreadsheet_id = st.secrets.connections.gsheets.spreadsheet.split("/d/")[1].split("/")[0]
    sheet = get_sheet_service()
    
    # 1. ניקוי הגיליון לחלוטין לפני הכתיבה כדי למנוע "שורות רפאים"
    sheet.values().clear(spreadsheetId=spreadsheet_id, range="sheet1!A:B").execute()
    
    # 2. כתיבת הנתונים המעודכנים
    body = {'values': [df.columns.tolist()] + df.values.tolist()}
    sheet.values().update(
        spreadsheetId=spreadsheet_id, range="sheet1!A1",
        valueInputOption="RAW", body=body).execute()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("📝 מערכת איסוף מחשבות לוועדה")

meetings = ["מפגש התנעה", "מפגש שני", "מפגש שלישי", "מפגש רביעי", "מפגש חמישי", "מפגש שישי", "מפגש שביעי", "מפגש שמיני"]
meeting_id = st.selectbox("בחר מפגש:", options=meetings)

if meeting_id:
    df = read_data()
    # סינון התגובות עבור המפגש הנבחר
    filtered_df = df[df['meeting'] == meeting_id] if not df.empty else pd.DataFrame()

    with st.form("add_thought", clear_on_submit=True):
        msg = st.text_area(f"מה המחשבה שלך על {meeting_id}?")
        if st.form_submit_button("שלח מחשבה"):
            if msg:
                new_row = pd.DataFrame([{"meeting": meeting_id, "thought": msg}])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success("נשמר!")
                st.rerun()

    st.divider()

    # אזור מנהל
    with st.sidebar:
        st.header("🔐 ניהול")
        if st.text_input("סיסמה:", type="password") == "1234":
            st.session_state['admin'] = True
    
    if st.session_state.get('admin'):
        if st.button(f"🪄 סכם AI - {meeting_id}"):
            thoughts = filtered_df['thought'].tolist() if not filtered_df.empty else []
            if thoughts:
                res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": f"סכם את המחשבות מ{meeting_id}:\n" + "\n".join(thoughts)}]
                )
                st.info(res.choices[0].message.content)

        st.subheader(f"🗑️ ניהול תגובות")
        if not filtered_df.empty:
            for idx, row in filtered_df.iterrows():
                # טיפול בתצוגת None
                display_text = str(row['thought']) if pd.notnull(row['thought']) else "תגובה ריקה"
                col1, col2 = st.columns([0.8, 0.2])
                col1.write(f"{display_text}")
                if col2.button("מחק", key=f"del_{idx}"):
                    # מחיקה לפי אינדקס מקורי ב-df
                    df = df.drop(idx)
                    save_data(df)
                    st.success("נמחק בהצלחה!")
                    st.rerun()
