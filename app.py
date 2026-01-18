import streamlit as st
import pandas as pd
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

# --- פונקציות גוגל (כבר עובדות!) ---
def get_sheet_service():
    sa_info = json.loads(st.secrets.connections.gsheets.service_account)
    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    return build('sheets', 'v4', credentials=creds).spreadsheets()

def read_data():
    try:
        spreadsheet_id = st.secrets.connections.gsheets.spreadsheet.split("/d/")[1].split("/")[0]
        res = get_sheet_service().values().get(spreadsheetId=spreadsheet_id, range="sheet1!A:B").execute()
        vals = res.get('values', [])
        return pd.DataFrame(vals[1:], columns=vals[0]) if vals else pd.DataFrame(columns=["meeting", "thought"])
    except: return pd.DataFrame(columns=["meeting", "thought"])

def save_data(df):
    spreadsheet_id = st.secrets.connections.gsheets.spreadsheet.split("/d/")[1].split("/")[0]
    service = get_sheet_service()
    service.values().clear(spreadsheetId=spreadsheet_id, range="sheet1!A:B").execute()
    body = {'values': [df.columns.tolist()] + df.values.tolist()}
    service.values().update(spreadsheetId=spreadsheet_id, range="sheet1!A1", valueInputOption="RAW", body=body).execute()

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
                save_data(pd.concat([df, new_row], ignore_index=True))
                st.success("נשמר!")
                st.rerun()

    with st.sidebar:
        st.header("🔐 ניהול")
        pwd = st.text_input("סיסמה:", type="password")
        if pwd == "1234":
            if st.button(f"🪄 סכם AI - {meeting_id}"):
                thoughts = df[df['meeting'] == meeting_id]['thought'].tolist()
                if thoughts:
                    try:
                        # וידוא שהמפתח נמשך ללא רווחים מיותרים
                        api_key = st.secrets["OPENAI_API_KEY"].strip()
                        
                        # דיבאג (יוצג רק לך): מוודא שהמפתח מסתיים ב-jUkA
                        # st.write(f"DEBUG: Key ends with {api_key[-4:]}") 

                        client = OpenAI(api_key=api_key)
                        res = client.chat.completions.create(
                            model="gpt-4o", 
                            messages=[{"role": "user", "content": f"סכם לנקודות את המחשבות מ{meeting_id}:\n" + "\n".join(thoughts)}]
                        )
                        st.info(f"סיכום {meeting_id}:")
                        st.write(res.choices[0].message.content)
                    except Exception as e:
                        st.error(f"שגיאת אימות OpenAI: {e}")
                else:
                    st.warning("אין תגובות לסיכום.")

            st.subheader("🗑️ ניהול תגובות")
            filtered = df[df['meeting'] == meeting_id]
            for idx, row in filtered.iterrows():
                col1, col2 = st.columns([0.8, 0.2])
                col1.write(str(row['thought']))
                if col2.button("מחק", key=f"del_{idx}"):
                    save_data(df.drop(idx))
                    st.rerun()
