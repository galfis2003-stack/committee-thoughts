import streamlit as st
import pandas as pd
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

# --- פונקציות גוגל (התיקון ל-ValueError) ---
def get_sheet_service():
    # שליפת המידע מה-Secrets
    raw_sa = st.secrets.connections.gsheets.service_account
    
    # וידוא שהפורמט הוא Dictionary (פותר את ה-ValueError משורה 13)
    if isinstance(raw_sa, str):
        sa_info = json.loads(raw_sa)
    else:
        sa_info = dict(raw_sa)
    
    # תיקון קריטי למפתח הפרטי - החלפת תווי n\\ בתו ירידת שורה אמיתי
    if "private_key" in sa_info:
        sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")
    
    creds = service_account.Credentials.from_service_account_info(
        sa_info, 
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return build('sheets', 'v4', credentials=creds, cache_discovery=False).spreadsheets()

def read_data():
    try:
        spreadsheet_id = st.secrets.connections.gsheets.spreadsheet.split("/d/")[1].split("/")[0]
        res = get_sheet_service().values().get(spreadsheetId=spreadsheet_id, range="sheet1!A:B").execute()
        vals = res.get('values', [])
        return pd.DataFrame(vals[1:], columns=vals[0]) if vals else pd.DataFrame(columns=["meeting", "thought"])
    except Exception as e:
        st.error(f"שגיאת קריאה: {e}")
        return pd.DataFrame(columns=["meeting", "thought"])

def save_data(df):
    try:
        spreadsheet_id = st.secrets.connections.gsheets.spreadsheet.split("/d/")[1].split("/")[0]
        service = get_sheet_service()
        # ניקוי הגיליון לפני כתיבה למניעת כפילויות
        service.values().clear(spreadsheetId=spreadsheet_id, range="sheet1!A:B").execute()
        body = {'values': [df.columns.tolist()] + df.values.tolist()}
        service.values().update(spreadsheetId=spreadsheet_id, range="sheet1!A1", valueInputOption="RAW", body=body).execute()
        return True
    except Exception as e:
        st.error(f"שגיאת שמירה: {e}")
        return False

# --- ממשק משתמש ---
st.title("📝 מערכת איסוף מחשבות לוועדה")

meetings = ["מפגש התנעה", "מפגש שני", "מפגש שלישי", "מפגש רביעי", "מפגש חמישי", "מפגש שישי", "מפגש שביעי", "מפגש שמיני"]
meeting_id = st.selectbox("בחר מפגש:", options=meetings)

if meeting_id:
    df = read_data()
    with st.form("add_thought", clear_on_submit=True):
        msg = st.text_area(f"מה המחשבה שלך על {meeting_id}?")
        if st.form_submit_button("שלח מחשבה"):
            if msg:
                new_row = pd.DataFrame([{"meeting": meeting_id, "thought": msg}])
                success = save_data(pd.concat([df, new_row], ignore_index=True))
                if success:
                    st.success("המחשבה נשמרה בגיליון!")
                    st.rerun()

    # אזור ניהול
    with st.sidebar:
        st.header("🔐 ניהול")
        if st.text_input("סיסמה:", type="password") == "1234":
            if st.button(f"🪄 סכם AI - {meeting_id}"):
                thoughts = df[df['meeting'] == meeting_id]['thought'].tolist()
                if thoughts:
                    try:
                        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"].strip())
                        res = client.chat.completions.create(
                            model="gpt-4o", 
                            messages=[{"role": "user", "content": f"סכם לנקודות את {meeting_id}:\n" + "\n".join(thoughts)}]
                        )
                        st.info(res.choices[0].message.content)
                    except Exception as e:
                        st.error(f"שגיאת AI: {e}")

            st.subheader("🗑️ ניהול תגובות")
            filtered = df[df['meeting'] == meeting_id]
            for idx, row in filtered.iterrows():
                col1, col2 = st.columns([0.8, 0.2])
                col1.write(str(row['thought']))
                if col2.button("מחק", key=f"del_{idx}"):
                    save_data(df.drop(idx))
                    st.rerun()
