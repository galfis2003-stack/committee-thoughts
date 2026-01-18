import streamlit as st
from openai import OpenAI

# הגדרת כותרת האתר
st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

# חיבור ל-OpenAI דרך ה-Secrets שהגדרת
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("📝 מערכת איסוף מחשבות לוועדה")

# --- בעיה 2: כניסה לפי מספר פגישה ---
meeting_id = st.text_input("הכנס מספר פגישה (למשל: 101):")

if meeting_id:
    st.subheader(f"מחשבות עבור פגישה מספר {meeting_id}")
    
    # זיכרון זמני (יוחלף בהמשך ב-Google Sheets לשמירה קבועה)
    if "thoughts" not in st.session_state:
        st.session_state.thoughts = []

    # הזנת מחשבה חדשה
    with st.form("thought_form", clear_on_submit=True):
        new_thought = st.text_area("מה המחשבה שלך בנושא הדיון?")
        submitted = st.form_submit_button("שלח מחשבה")
        
        if submitted and new_thought:
            st.session_state.thoughts.append(new_thought)
            st.success("המחשבה נשמרה בהצלחה!")

    st.divider()

    # --- בעיה 3: הרשאת מנהל לייצוא סיכום ---
    with st.sidebar:
        st.header("אזור מנהל")
        admin_password = st.text_input("סיסמת מנהל לייצוא סיכום:", type="password")
    
    # כאן אתה קובע את הסיסמה שלך (למשל: 1234)
    if admin_password == "1234": 
        if st.button("🪄 ייצר סיכום AI (למנהל בלבד)"):
            if st.session_state.thoughts:
                with st.spinner("ה-AI מנתח את כל המחשבות..."):
                    all_text = "\n".join(st.session_state.thoughts)
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "אתה עוזר מקצועי לוועדה. סכם את המחשבות הבאות לנקודות מרכזיות."},
                            {"role": "user", "content": f"להלן המחשבות מפגישה {meeting_id}:\n{all_text}"}
                        ]
                    )
                    st.info("סיכום הוועדה:")
                    st.write(response.choices[0].message.content)
            else:
                st.warning("עדיין אין מחשבות לסכם.")
    elif admin_password:
        st.sidebar.error("סיסמה שגויה")
else:
    st.info("אנא הכנס מספר פגישה כדי להתחיל.")
