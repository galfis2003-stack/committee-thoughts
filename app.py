import streamlit as st
import pandas as pd
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

# הגדרות עמוד
st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

# --- פונקציות חיבור ידניות (כי הן עובדות!) ---
def get_sheet_service():
    sa_info = json.loads(st.secrets.connections.gsheets.service_account)
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=scopes)
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()

def read_data():
    spreadsheet_id = st.secrets.connections.gsheets.spreadsheet.split("/d/")[1].split("/")[0]
    sheet = get_sheet_service()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range="sheet1!A:B").execute()
    values = result.get('values', [])
    if not values:
        return pd.DataFrame(columns=["meeting", "thought"])
    return pd.DataFrame(values[1:], columns=values[0])

def save_data(df):
    spreadsheet_id = st.secrets.connections.gsheets.spreadsheet.split("/d/")[1].split("/")[0]
    sheet = get_sheet_service()
    # כתיבת כל הטבלה מחדש (כולל כותרות) כדי להבטיח סנכרון
    body = {'values': [df.columns.tolist()] + df.values.tolist()}
    sheet.values().update(
        spreadsheetId=spreadsheet_id, range="sheet1!A1",
        valueInputOption="RAW", body=body).execute()

# אתחול OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("📝 מערכת איסוף מחשבות לוועדה")

meetings = ["מפגש התנעה", "מפגש שני", "מפגש שלישי", "מפגש רביעי", "מפגש חמישי", "מפגש שישי", "מפגש שביעי", "מפגש שמיני"]
meeting_id = st.selectbox("בחר את המפגש הרלוונטי:", options=meetings)

if meeting_id:
    df = read_data()
    current_thoughts = df[df['meeting'] == meeting_id]['thought'].tolist() if not df.empty else []

    with st.form("add_thought", clear_on_submit=True):
        msg = st.text_area(f"מה המחשבה שלך על {meeting_id}?")
        if st.form_submit_button("שלח מחשבה"):
            if msg:
                new_row = pd.DataFrame([{"meeting": meeting_id, "thought": msg}])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                save_data(updated_df)
                st.success("המחשבה נשמרה בענן!")
                st.rerun()

    st.divider()

    # אזור מנהל בסרגל הצד
    with st.sidebar:
        st.header("🔐 ניהול")
        pwd = st.text_input("סיסמה:", type="password")
    
    if pwd == "1234":
        if st.button(f"🪄 סכם AI עבור {meeting_id}"):
            if current_thoughts:
                with st.spinner("מנתח..."):
                    res = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": f"סכם את {meeting_id} לנקודות מרכזיות:\n" + "\n".join(current_thoughts)}]
                    )
                    st.info(f"סיכום {meeting_id}:")
                    st.write(res.choices[0].message.content)
            else:
                st.warning("אין תגובות לסיכום.")

        st.subheader("🗑️ מחיקת תגובות")
        if current_thoughts:
            for i, t in enumerate(current_thoughts):
                col1, col2 = st.columns([0.8, 0.2])
                col1.write(f"{i+1}. {t}")
                if col2.button("מחק", key=f"del_{i}"):
                    # מציאת האינדקס המקורי ומחיקה
                    df = df.drop(df[(df['meeting'] == meeting_id) & (df['thought'] == t)].index[0])
                    save_data(df)
                    st.rerun()
