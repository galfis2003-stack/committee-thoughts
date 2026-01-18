import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="מחשבות הוועדה", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
conn = st.connection("gsheets", type=GSheetsConnection)

# וודא ששם זה תואם בדיוק לשונית למטה (למשל: "Sheet1" או "גיליון1")
WORKSHEET_NAME = "גיליון1" 

def get_data():
    try:
        return conn.read(worksheet=WORKSHEET_NAME, ttl="0s")
    except:
        return pd.DataFrame(columns=["meeting", "thought"])

st.title("📝 מערכת איסוף מחשבות לוועדה")

meetings = ["מפגש התנעה", "מפגש שני", "מפגש שלישי", "מפגש רביעי", "מפגש חמישי", "מפגש שישי", "מפגש שביעי", "מפגש שמיני"]
meeting_id = st.selectbox("בחר מפגש:", options=meetings)

if meeting_id:
    df = get_data()
    current_thoughts = df[df['meeting'] == meeting_id]['thought'].tolist() if not df.empty else []

    with st.form("add_thought", clear_on_submit=True):
        msg = st.text_area(f"מה המחשבה שלך על {meeting_id}?")
        if st.form_submit_button("שלח מחשבה"):
            if msg:
                new_row = pd.DataFrame([{"meeting": meeting_id, "thought": msg}])
                # חיבור הנתונים החדשים לטבלה הקיימת
                updated_df = pd.concat([df, new_row], ignore_index=True) if not df.empty else new_row
                
                # ביצוע העדכון לענן עם ציון מפורש של הגיליון
                conn.update(worksheet=WORKSHEET_NAME, data=updated_df)
                st.success("נשמר בהצלחה!")
                st.rerun()

    # אזור מנהל
    st.sidebar.header("🔐 ניהול")
    pwd = st.sidebar.text_input("סיסמה:", type="password")
    if pwd == "1234":
        if st.button("🪄 סכם AI"):
            if current_thoughts:
                res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": f"סכם את {meeting_id}:\n" + "\n".join(current_thoughts)}]
                )
                st.info(res.choices[0].message.content)
