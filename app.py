import streamlit as st
from openai import OpenAI

# הגדרת כותרת האתר
st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

# חיבור ל-OpenAI דרך ה-Secrets שהגדרת
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("📝 מערכת איסוף מחשבות לוועדה")

# --- רשימת המפגשים ---
meeting_options = [
    "מפגש התנעה", "מפגש שני", "מפגש שלישי", "מפגש רביעי", 
    "מפגש חמישי", "מפגש שישי", "מפגש שביעי", "מפגש שמיני"
]
meeting_id = st.selectbox("בחר את המפגש הרלוונטי:", options=meeting_options)

# --- ניהול הזיכרון לפי מפתח (Meeting ID) ---
if "all_meetings_data" not in st.session_state:
    # יוצר מילון שבו לכל מפגש יש רשימת מחשבות משלו
    st.session_state.all_meetings_data = {m: [] for m in meeting_options}

if meeting_id:
    st.subheader(f"מחשבות עבור {meeting_id}")
    
    # שליפת המחשבות הספציפיות למפגש שנבחר
    current_thoughts = st.session_state.all_meetings_data[meeting_id]

    # הזנת מחשבה חדשה
    with st.form("thought_form", clear_on_submit=True):
        new_thought = st.text_area(f"מה המחשבה שלך בנוגע ל-{meeting_id}?")
        submitted = st.form_submit_button("שלח מחשבה")
        
        if submitted and new_thought:
            st.session_state.all_meetings_data[meeting_id].append(new_thought)
            st.success(f"המחשבה נשמרה ב-{meeting_id}!")
            st.rerun() # רענון כדי להציג את התגובה החדשה מיד

    st.divider()

    # --- אזור מנהל ---
    with st.sidebar:
        st.header("אזור מנהל")
        admin_password = st.text_input("סיסמת מנהל לניהול המערכת:", type="password")
    
    if admin_password == "1234": 
        st.sidebar.success("מצב מנהל פעיל")
        
        # 1. סיכום AI ספציפי למפגש
        if st.button(f"🪄 ייצר סיכום AI ל-{meeting_id}"):
            if current_thoughts:
                with st.spinner(f"ה-AI מנתח את המחשבות של {meeting_id}..."):
                    all_text = "\n".join(current_thoughts)
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": f"אתה עוזר מקצועי לוועדה. סכם את המחשבות מ{meeting_id} בלבד."},
                            {"role": "user", "content": f"להלן המחשבות:\n{all_text}"}
                        ]
                    )
                    st.info(f"סיכום עבור {meeting_id}:")
                    st.write(response.choices[0].message.content)
            else:
                st.warning(f"אין עדיין מחשבות לסכם עבור {meeting_id}.")
        
        st.divider()
        
        # 2. ניהול ומחיקת תגובות ספציפיות
        st.subheader(f"🗑️ ניהול תגובות - {meeting_id}")
        if current_thoughts:
            for i, thought in enumerate(current_thoughts):
                col1, col2 = st.columns([0.85, 0.15])
                col1.write(f"**{i+1}.** {thought}")
                if col2.button("מחק", key=f"del_{meeting_id}_{i}"):
                    st.session_state.all_meetings_data[meeting_id].pop(i)
                    st.rerun() 
        else:
            st.write("אין תגובות במפגש זה.")
