import streamlit as st
import pandas as pd
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

# --- דיאגנוסטיקה: בדיקה שה-Secrets קיימים לפני שמתחילים ---
if "connections" not in st.secrets:
    st.error("❌ שגיאה קריטית: חסרה הכותרת [connections.gsheets] ב-Secrets.")
    st.stop()

if "gsheets" not in st.secrets.connections:
    st.error("❌ שגיאה קריטית: חסר החלק של gsheets ב-Secrets.")
    st.stop()

# --- פונקציות גוגל (הגרסה החסינה ביותר) ---
def get_sheet_service():
    try:
        # שליפת המידע הגולמי
        raw_sa = st.secrets.connections.gsheets.service_account
        
        # המרה ל-Dictionary (בין אם זה טקסט או כבר אובייקט)
        if isinstance(raw_sa, str):
            sa_info = json.loads(raw_sa)
        else:
            sa_info = dict(raw_sa)
        
        # וידוא שהמפתח הפרטי תקין
        if "private_key" in sa_info:
            sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")
        
        creds = service_account.Credentials.from_service_account_info(
            sa_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        return build('sheets', 'v4', credentials=creds, cache_discovery=False).spreadsheets()
    except Exception as e:
        st.error(f"❌ שגיאה בחיבור לגוגל: {e}")
        st.stop()

def read_data():
    try:
        spreadsheet_id = st.secrets.connections.gsheets.spreadsheet.split("/d/")[1].split("/")[0]
        service = get_sheet_service()
        res = service.values().get(spreadsheetId=spreadsheet_id, range="sheet1!A:B").execute()
        vals = res.get('values', [])
        if vals and len(vals) > 0:
            return pd.DataFrame(vals[1:], columns=vals[0])
        else:
            return pd.DataFrame(columns=["meeting", "thought"])
    except Exception as e:
        # אם יש שגיאה, נחזיר טבלה ריקה כדי שהאתר לא יקרוס
        return pd.DataFrame(columns=["meeting", "thought"])

def save_data(df):
    try:
        spreadsheet_id = st.secrets.connections.gsheets.spreadsheet.split("/d/")[1].split("/")[0]
        service = get_sheet_service()
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
        submitted = st.form_submit_button("שלח מחשבה")
        if submitted and msg:
            new_row = pd.DataFrame([{"meeting": meeting_id, "thought": msg}])
            success = save_data(pd.concat([df, new_row], ignore_index=True))
            if success:
                st.success("נשמר בהצלחה!")
                st.rerun()

    with st.sidebar:
        st.header("🔐 ניהול")
        if st.text_input("סיסמה:", type="password") == "1234":
            if st.button(f"🪄 סכם AI - {meeting_id}"):
                thoughts = df[df['meeting'] == meeting_id]['thought'].tolist()
                if thoughts:
                    try:
                        api_key = st.secrets["OPENAI_API_KEY"].strip()
                        client = OpenAI(api_key=api_key)
                        res = client.chat.completions.create(
                            model="gpt-4o", 
                            messages=[{"role": "user", "content": f"סכם לנקודות את {meeting_id}:\n" + "\n".join(thoughts)}]
                        )
                        st.info(res.choices[0].message.content)
                    except Exception as e:
                        st.error(f"שגיאת AI: {e}")
