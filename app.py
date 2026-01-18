import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# הגדרות עמוד
st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

# אתחול חיבורים מה-Secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
conn = st.connection("gsheets", type=GSheetsConnection)

# --- הגדרה מדויקת לפי התיקון שלך ---
WORKSHEET_NAME = "sheet1" 

def get_data():
    try:
        # קריאה ישירה מהטאב הנכון
        return conn.read(worksheet=WORKSHEET_NAME, ttl="0s")
    except:
        # יצירת מבנה בסיסי אם הגיליון ריק
        return pd.DataFrame(columns=["meeting", "thought"])

st.title("📝 מערכת איסוף מחשבות לוועדה")

# רשימת המפגשים
meetings = ["מפגש התנעה", "מפגש שני", "מפגש שלישי", "מפגש רביעי", "מפגש חמישי", "מפגש שישי", "מפגש שביעי", "מפגש שמיני"]
meeting_id = st.selectbox("בחר את המפגש הרלוונטי:", options=meetings)

if meeting_id:
    df = get_data()
    # סינון תגובות לפי המפגש הנבחר
    current_thoughts = df[df['meeting'] == meeting_id]['thought'].tolist() if not df.empty else []

    st.subheader(f"הזנת מחשבה - {meeting_id}")
    with st.form("add_thought", clear_on_submit=True):
        msg = st.text_area("מה המחשבה שלך בנושא הדיון?")
        if st.form_submit_button("שלח מחשבה"):
            if msg:
                new_row = pd.DataFrame([{"meeting": meeting_id, "thought": msg}])
                updated_df = pd.concat([df, new_row], ignore_index=True) if not df.empty else new_row
                
                # כתיבה לגיליון בענן
                conn.update(worksheet=WORKSHEET_NAME, data=updated_df)
                st.success("המחשבה נשמרה בענן בהצלחה!")
                st.rerun()

    st.divider()

    # --- אזור מנהל ---
    st.sidebar.header("🔐 אזור מנהל")
    pwd = st.sidebar.text_input("הזן סיסמה:", type="password")
    
    if pwd == "1234":
        st.sidebar.success("מצב מנהל פעיל")
        
        # סיכום AI
        if st.button(f"🪄 סכם AI עבור {meeting_id}"):
            if current_thoughts:
                with st.spinner("מנתח נתונים..."):
                    all_text = "\n".join(current_thoughts)
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": f"אתה עוזר מקצועי לוועדה. סכם את המחשבות מ{meeting_id} לנקודות מרכזיות."},
                            {"role": "user", "content": all_text}
                        ]
                    )
                    st.info(f"סיכום {meeting_id}:")
                    st.write(response.choices[0].message.content)
            else:
                st.warning("אין תגובות לסיכום במפגש זה.")

        # ניהול ומחיקה
        st.subheader(f"🗑️ ניהול תגובות - {meeting_id}")
        if current_thoughts:
            for i, t in enumerate(current_thoughts):
                col1, col2 = st.columns([0.85, 0.15])
                col1.write(f"**{i+1}.** {t}")
                if col2.button("מחק", key=f"del_{i}"):
                    # מחיקה מהענן
                    index_to_drop = df[(df['meeting'] == meeting_id) & (df['thought'] == t)].index[0]
                    df = df.drop(index_to_drop)
                    conn.update(worksheet=WORKSHEET_NAME, data=df)
                    st.rerun()
        else:
            st.write("אין כרגע תגובות שמורות.")
