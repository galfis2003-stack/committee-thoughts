import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="מחשבות הוועדה", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# חיבור לגוגל שיטס
conn = st.connection("gsheets", type=GSheetsConnection)

# הגדרה מדויקת של שם הגיליון (וודא שזה מה שכתוב בלשונית למטה)
WORKSHEET_NAME = "sheet1" 

def get_data():
    try:
        # קריאה נקייה מהענן
        return conn.read(worksheet=WORKSHEET_NAME, ttl="0s")
    except:
        # אם הגיליון ריק, מחזירים מבנה עם הכותרות הנכונות
        return pd.DataFrame(columns=["meeting", "thought"])

st.title("📝 מערכת איסוף מחשבות לוועדה")

meetings = ["מפגש התנעה", "מפגש שני", "מפגש שלישי", "מפגש רביעי", "מפגש חמישי", "מפגש שישי", "מפגש שביעי", "מפגש שמיני"]
meeting_id = st.selectbox("בחר את המפגש:", options=meetings)

if meeting_id:
    df = get_data()
    
    with st.form("add_thought", clear_on_submit=True):
        msg = st.text_area(f"מה המחשבה שלך על {meeting_id}?")
        if st.form_submit_button("שלח מחשבה"):
            if msg:
                # 1. יצירת השורה החדשה
                new_data = {"meeting": meeting_id, "thought": msg}
                
                # 2. בניית DataFrame חדש ואיחוד עם הקיים
                new_row_df = pd.DataFrame([new_data])
                
                if df.empty:
                    updated_df = new_row_df
                else:
                    # מוודאים שסדר העמודות נשמר בדיוק כפי שמופיע בגיליון
                    updated_df = pd.concat([df, new_row_df], ignore_index=True)
                
                # 3. ניסיון עדכון עם טיפול בשגיאות מפורט
                try:
                    conn.update(worksheet=WORKSHEET_NAME, data=updated_df)
                    st.success("נשמר בהצלחה בענן!")
                    st.rerun()
                except Exception as e:
                    st.error("שגיאת כתיבה. נסה לרענן את הדף.")
                    st.sidebar.error(f"Error details: {e}")

    # אזור מנהל
    st.sidebar.header("🔐 ניהול")
    pwd = st.sidebar.text_input("סיסמה:", type="password")
    if pwd == "1234":
        if st.button("🪄 סכם AI"):
            # סינון מחשבות למפגש הנוכחי בלבד
            thoughts = df[df['meeting'] == meeting_id]['thought'].tolist() if not df.empty else []
            if thoughts:
                res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": f"סכם את {meeting_id}:\n" + "\n".join(thoughts)}]
                )
                st.info(res.choices[0].message.content)
            else:
                st.warning("אין תגובות לסיכום.")
