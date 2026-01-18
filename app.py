import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
conn = st.connection("gsheets", type=GSheetsConnection)

# הגדרה מדויקת לפי המבנה שלך
WORKSHEET_NAME = "sheet1" 

def get_data():
    try:
        return conn.read(worksheet=WORKSHEET_NAME, ttl="0s")
    except:
        return pd.DataFrame(columns=["meeting", "thought"])

st.title("📝 מערכת איסוף מחשבות לוועדה")

meetings = ["מפגש התנעה", "מפגש שני", "מפגש שלישי", "מפגש רביעי", "מפגש חמישי", "מפגש שישי", "מפגש שביעי", "מפגש שמיני"]
meeting_id = st.selectbox("בחר את המפגש הרלוונטי:", options=meetings)

if meeting_id:
    df = get_data()
    current_thoughts = df[df['meeting'] == meeting_id]['thought'].tolist() if not df.empty else []

    with st.form("add_thought", clear_on_submit=True):
        msg = st.text_area(f"מה המחשבה שלך בנושא {meeting_id}?")
        if st.form_submit_button("שלח מחשבה"):
            if msg:
                new_row = pd.DataFrame([{"meeting": meeting_id, "thought": msg}])
                updated_df = pd.concat([df, new_row], ignore_index=True) if not df.empty else new_row
                conn.update(worksheet=WORKSHEET_NAME, data=updated_df)
                st.success("המחשבה נשמרה בהצלחה!")
                st.rerun()

    st.divider()

    with st.sidebar:
        st.header("🔐 ניהול")
        pwd = st.text_input("סיסמה:", type="password")
    
    if pwd == "1234":
        if st.button(f"🪄 סכם AI עבור {meeting_id}"):
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
        if current_thoughts:
            for i, t in enumerate(current_thoughts):
                col1, col2 = st.columns([0.8, 0.2])
                col1.write(f"{i+1}. {t}")
                if col2.button("מחק", key=f"del_{i}"):
                    index_to_drop = df[(df['meeting'] == meeting_id) & (df['thought'] == t)].index[0]
                    df = df.drop(index_to_drop)
                    conn.update(worksheet=WORKSHEET_NAME, data=df)
                    st.rerun()
