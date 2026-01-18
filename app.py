import streamlit as st
from openai import OpenAI

# הגדרת כותרת האתר
st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

# חיבור ל-OpenAI דרך ה-Secrets שהגדרת
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("📝 מערכת איסוף מחשבות לוועדה")

# --- בחירה מרשימת פגישות ---
meeting_options = ["פגישה 1", "פגישה 2", "פגישה 3"]
meeting_id = st.selectbox("בחר מספר פגישה:", options=meeting_options)

if meeting_id:
    st.subheader(f"מחשבות עבור {meeting_id}")
    
    # זיכרון זמני (יוחלף בהמשך ב-Google Sheets לשמירה קבועה)
    if "thoughts" not in st.session_state:
        st.session_state.thoughts = []

    # הזנת מחשבה חדשה
    with st.form("thought_form", clear_on_submit=True):
        new_thought = st.text_area(f"מה המחשבה שלך בנוגע ל-{meeting_id}?")
        submitted = st.form_submit_button("שלח מחשבה")
        
        if submitted and new_thought:
            st.session_state.thoughts.append(new_thought)
            st.success("המחשבה נשמרה בהצלחה!")

    st.divider()

    # --- אזור מנהל ---
    with st.sidebar:
        st.header("אזור מנהל")
        admin_password = st.text_input("סיסמת מנהל לניהול המערכת:", type="password")
    
    # בדיקת סיסמה (כרגע מוגדרת כ-1234)
    if admin_password == "1234": 
        st.sidebar.success("מצב מנהל פעיל")
        
        # 1. כפתור ייצור סיכום AI
        if st.button("🪄 ייצר סיכום AI"):
            if st.session_state.thoughts:
                with st.spinner("ה-AI מנתח את כל המחשבות..."):
                    all_text = "\n".join(st.session_state.thoughts)
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "אתה עוזר מקצועי לוועדה. סכם את המחשבות הבאות לנקודות מרכזיות."},
                            {"role": "user", "content": f"להלן המחשבות מ{meeting_id}:\n{all_text}"}
                        ]
                    )
                    st.info("סיכום הוועדה:")
                    st.write(response.choices[0].message.content)
            else:
                st.warning("עדיין אין מחשבות לסכם.")
        
        st.divider()
        
        # 2. ניהול ומחיקת תגובות (חדש!)
        st.subheader("🗑️ ניהול ומחיקת תגובות")
        if st.session_state.thoughts:
            for i, thought in enumerate(st.session_state.thoughts):
                # יצירת שתי עמודות: אחת לטקסט ואחת לכפתור
                col1, col2 = st.columns([0.85, 0.15])
                col1.write(f"**{i+1}.** {thought}")
                # אם לוחצים על מחק, התגובה מוסרת מהרשימה והדף מתרענן
                if col2.button("מחק", key=f"del_{i}"):
                    st.session_state.thoughts.pop(i)
                    st.rerun() 
        else:
            st.write("אין כרגע תגובות במערכת.")
            
    elif admin_password:
        st.sidebar.error("סיסמה שגויה")
else:
    st.info("אנא הכנס מספר פגישה כדי להתחיל.")
