import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
conn = st.connection("gsheets", type=GSheetsConnection)

# --- זיהוי שם הגיליון ---
# אם כתוב לך "Sheet1" בטאב למטה, השאר ככה. אם כתוב "גיליון1", שנה.
WORKSHEET_NAME = "Sheet1" 

def get_data():
    try:
        # קריאה מפורשת למניעת שגיאות
        return conn.read(worksheet=WORKSHEET_NAME, ttl="0s")
    except Exception as e:
        # אם הגיליון ריק לגמרי או שיש שגיאת קריאה
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
                # איחוד הנתונים בצורה נקייה
                if df.empty:
                    updated_df = new_row
                else:
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                
                # העלאה מפורשת לטאב המבוקש
                conn.update(worksheet=WORKSHEET_NAME, data=updated_df)
                st.success("המחשבה נשמרה בענן!")
                st.rerun()

    st.sidebar.header("🔐 אזור מנהל")
    pwd = st.sidebar.text_input("סיסמה:", type="password")
    if pwd == "1234":
        if st.button("🪄 סכם AI"):
            if current_thoughts:
                with st.spinner("מנתח..."):
                    res = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": f"סכם את {meeting_id}:\n" + "\n".join(current_thoughts)}]
                    )
                    st.info(f"סיכום {meeting_id}:")
                    st.write(res.choices[0].message.content)
            else:
                st.warning("אין תגובות לסיכום.")

        st.subheader("🗑️ ניהול תגובות")
        for i, t in enumerate(current_thoughts):
            col1, col2 = st.columns([0.8, 0.2])
            col1.write(f"{i+1}. {t}")
            if col2.button("מחק", key=f"del_{i}"):
                # מציאת האינדקס של השורה הספציפית ומחיקה
                index_to_drop = df[(df['meeting'] == meeting_id) & (df['thought'] == t)].index[0]
                df = df.drop(index_to_drop)
                conn.update(worksheet=WORKSHEET_NAME, data=df)
                st.rerun()
