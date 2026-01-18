import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

# --- בדיקת דופק ל-Secrets ---
if "connections" not in st.secrets or "gsheets" not in st.secrets.connections:
    st.error("⚠️ תקלה: האפליקציה לא מוצאת את הגדרות הבוט ב-Secrets. וודא שהשתמשת בפורמט [connections.gsheets].")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
conn = st.connection("gsheets", type=GSheetsConnection)

# שימוש ב-sheet1 באות קטנה כפי שציינת
WORKSHEET_NAME = "sheet1" 

def get_data():
    try:
        return conn.read(worksheet=WORKSHEET_NAME, ttl="0s")
    except Exception as e:
        st.warning(f"שים לב: לא ניתן לקרוא נתונים מ-{WORKSHEET_NAME}. בדוק שהשם מדויק.")
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
                    # ניסיון עדכון
                    conn.update(worksheet=WORKSHEET_NAME, data=updated_df)
                    st.success("נשמר בהצלחה בענן!")
                    st.rerun()
                except Exception as e:
                    st.error("שגיאת כתיבה: הגיליון מזוהה כציבורי (Public).")
                    st.info("💡 פתרון: וודא ששיתפת את הגיליון עם האימייל של הבוט בתור Editor.")
                    st.code(str(e))

    # אזור מנהל
    st.sidebar.header("🔐 ניהול")
    pwd = st.sidebar.text_input("סיסמה:", type="password")
    if pwd == "1234":
        if st.button("🪄 סכם AI"):
            thoughts = df[df['meeting'] == meeting_id]['thought'].tolist() if not df.empty else []
            if thoughts:
                res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": f"סכם את {meeting_id}:\n" + "\n".join(thoughts)}]
                )
                st.info(res.choices[0].message.content)
