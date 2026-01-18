import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

# אתחול
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
conn = st.connection("gsheets", type=GSheetsConnection)

# השם שצילמת
WORKSHEET_NAME = "sheet1" 

def get_data():
    try:
        # קריאה ישירה לדיבאג
        return conn.read(worksheet=WORKSHEET_NAME, ttl="0s")
    except Exception as e:
        st.error(f"שגיאת קריאה: {e}")
        return pd.DataFrame(columns=["meeting", "thought"])

st.title("📝 מערכת איסוף מחשבות לוועדה")

meetings = ["מפגש התנעה", "מפגש שני", "מפגש שלישי", "מפגש רביעי", "מפגש חמישי", "מפגש שישי", "מפגש שביעי", "מפגש שמיני"]
meeting_id = st.selectbox("בחר מפגש:", options=meetings)

if meeting_id:
    df = get_data()
    
    with st.form("add_thought", clear_on_submit=True):
        msg = st.text_area(f"מה המחשבה שלך על {meeting_id}?")
        if st.form_submit_button("שלח מחשבה"):
            if msg:
                new_row = pd.DataFrame([{"meeting": meeting_id, "thought": msg}])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                
                try:
                    # ניסיון עדכון לענן
                    conn.update(worksheet=WORKSHEET_NAME, data=updated_df)
                    st.success("נשמר בהצלחה!")
                    st.rerun()
                except Exception as e:
                    st.error("נכשלה הכתיבה לגיליון.")
                    st.code(str(e))
