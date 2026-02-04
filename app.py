import streamlit as st
import pandas as pd
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

# --- בדיקות מקדימות למניעת קריסה ---
if "connections" not in st.secrets or "gsheets" not in st.secrets.connections:
    st.error("❌ שגיאה: הגדרות ה-Secrets אינן תקינות.")
    st.stop()

# --- פונקציות גוגל (הגרסה היציבה) ---
def get_sheet_service():
    try:
        raw_sa = st.secrets.connections.gsheets.service_account
        # המרה ל-Dictionary וטיפול בפורמטים שונים
        if isinstance(raw_sa, str):
            sa_info = json.loads(raw_sa)
        else:
            sa_info = dict(raw_sa)
        
        # תיקון המפתח הפרטי
        if "private_key" in sa_info:
            sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")
        
        creds = service_account.Credentials.from_service_account_info(
            sa_info, scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        return build('sheets', 'v4', credentials=creds, cache_discovery=False).spreadsheets()
    except Exception as e:
        st.error(f"שגיאת חיבור לגוגל: {e}")
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
    except:
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
    # טעינת הנתונים
    df = read_data()
    
    # טופס להוספת מחשבה (גלוי לכולם)
    with st.form("add_thought", clear_on_submit=True):
        msg = st.text_area(f"מה המחשבה שלך על {meeting_id}?")
        if st.form_submit_button("שלח מחשבה"):
            if msg:
                new_row = pd.DataFrame([{"meeting": meeting_id, "thought": msg}])
                if save_data(pd.concat([df, new_row], ignore_index=True)):
                    st.success("התגובה נשמרה בהצלחה!")
                    st.rerun()

    # --- אזור המנהל (גלוי רק עם סיסמה) ---
    with st.sidebar:
        st.header("🔐 כניסת מנהל")
        pwd = st.text_input("סיסמה:", type="password")
        
        if pwd == "1234":
            st.success(f"מחובר כמנהל")
            st.markdown("---")
            
            # סינון התגובות למפגש הנוכחי
            current_thoughts = df[df['meeting'] == meeting_id]
            thought_list = current_thoughts['thought'].tolist()
            
            # 1. כפתור סיכום AI
            if st.button(f"✨ סכם את {len(thought_list)} התגובות"):
                if thought_list:
                    try:
                        api_key = st.secrets["OPENAI_API_KEY"].strip()
                        client = OpenAI(api_key=api_key)
                        with st.spinner("ה-AI מסכם..."):
                            res = client.chat.completions.create(
                                model="gpt-4o", 
                                messages=[{"role": "user", "content": f"סכם בנקודות קצרות את המחשבות הבאות ממפגש '{meeting_id}':\n" + "\n".join(thought_list)}]
                            )
                            st.markdown("### 📝 סיכום AI:")
                            st.info(res.choices[0].message.content)
                    except Exception as e:
                        st.error(f"שגיאת AI: {e}")
                else:
                    st.warning("אין תגובות לסכם.")

            st.markdown("---")
            st.subheader(f"👀 צפייה בתגובות ({len(thought_list)})")
            
            # 2. הצגת התגובות אחת-אחת עם אפשרות מחיקה
            if not current_thoughts.empty:
                for idx, row in current_thoughts.iterrows():
                    with st.expander(f"תגובה {idx+1}", expanded=True):
                        st.write(row['thought'])
                        if st.button("🗑️ מחק", key=f"del_{idx}"):
                            new_df = df.drop(idx)
                            save_data(new_df)
                            st.rerun()
            else:
                st.write("עדיין אין תגובות למפגש זה.")
